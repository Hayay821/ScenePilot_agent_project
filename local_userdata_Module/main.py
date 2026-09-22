import secrets
import time
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

try:
    from .config import settings
    from .storage import Storage
except ImportError:
    from config import settings
    from storage import Storage


app = FastAPI(title="BoldMaker Local User Data API", version="0.1.0")
origins = [item.strip() for item in settings.cors_origins.split(",") if item.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins or ["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
storage = Storage(settings.data_root)
sessions: Dict[str, Dict[str, Any]] = {}


class LoginRequest(BaseModel):
    account: str
    password: str


class CloudLoginRequest(BaseModel):
    uid: str = Field(min_length=1, max_length=128)


class UpdateModel(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    original_name: Optional[str] = None
    is_public: Optional[bool] = None


def _session_user(authorization: Optional[str]) -> Optional[str]:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    session = sessions.get(authorization[7:].strip())
    if not session or session["expires"] < time.time():
        return None
    return session["uid"]


def current_user(authorization: Optional[str] = Header(None), x_user_id: Optional[str] = Header(None)) -> str:
    user_id = _session_user(authorization)
    if user_id:
        return user_id
    if settings.allow_uid_header and x_user_id:
        user_id = _validate_uid(x_user_id)
        storage.ensure_user(user_id)
        return user_id
    raise HTTPException(401, "请先登录或提供有效的 Bearer token")


def _validate_uid(uid: str) -> str:
    if not uid or len(uid) > 128 or uid in {".", ".."} or "/" in uid or "\\" in uid or "\x00" in uid:
        raise HTTPException(400, "uid 不合法")
    return uid


def _session(uid: str) -> Dict[str, str]:
    storage.ensure_user(uid)
    token = secrets.token_urlsafe(32)
    sessions[token] = {"uid": uid, "expires": time.time() + settings.session_ttl_hours * 3600}
    return {"access_token": token, "token_type": "bearer", "uid": uid}


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/login")
def login(payload: LoginRequest) -> Dict[str, str]:
    if payload.account != settings.test_account or payload.password != settings.test_password:
        raise HTTPException(401, "账号或密码错误")
    return _session(settings.test_uid)


@app.post("/api/auth/cloud-login")
def cloud_login(payload: CloudLoginRequest) -> Dict[str, str]:
    return _session(_validate_uid(payload.uid))


@app.post("/api/auth/logout")
def logout(authorization: Optional[str] = Header(None), user_id: str = Depends(current_user)) -> Dict[str, str]:
    if authorization and authorization.lower().startswith("bearer "):
        sessions.pop(authorization[7:].strip(), None)
    return {"status": "ok", "uid": user_id}


@app.get("/api/auth/me")
def me(user_id: str = Depends(current_user)) -> Dict[str, str]:
    return {"uid": user_id}


@app.get("/api/resources")
def list_resources(kind: Optional[str] = Query(None, pattern="^(image|video)$"), user_id: str = Depends(current_user)):
    return {"items": storage.list_resources(user_id, kind)}


@app.post("/api/resources", status_code=201)
async def upload_resource(file: UploadFile = File(...), kind: Optional[str] = Query(None), description: str = Query(""), user_id: str = Depends(current_user)):
    actual_kind = kind or ("video" if (file.content_type or "").startswith("video/") else "image" if (file.content_type or "").startswith("image/") else None)
    if actual_kind not in {"image", "video"}:
        raise HTTPException(400, "kind 必须是 image 或 video，且文件类型需要匹配")
    if kind and file.content_type and not file.content_type.startswith(f"{kind}/"):
        raise HTTPException(400, "kind 与文件 MIME 类型不匹配")
    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, "文件超过大小限制")
    try:
        return storage.save_resource(user_id, actual_kind, file.filename or "unnamed", file.content_type, data, description)
    except FileExistsError as error:
        raise HTTPException(409, str(error)) from error
    except ValueError as error:
        raise HTTPException(400, str(error)) from error


@app.get("/api/resources/{resource_id}")
def get_resource(resource_id: str, user_id: str = Depends(current_user)):
    item = storage.get_resource(user_id, resource_id)
    if not item:
        raise HTTPException(404, "资源不存在")
    return item


@app.put("/api/resources/{resource_id}")
def update_resource(resource_id: str, payload: UpdateModel, user_id: str = Depends(current_user)):
    try:
        item = storage.update_resource(user_id, resource_id, payload.model_dump(exclude_none=True))
    except FileExistsError as error:
        raise HTTPException(409, str(error)) from error
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    if not item:
        raise HTTPException(404, "资源不存在")
    return item


@app.delete("/api/resources/{resource_id}", status_code=204)
def delete_resource(resource_id: str, user_id: str = Depends(current_user)):
    if not storage.delete_resource(user_id, resource_id):
        raise HTTPException(404, "资源不存在")


@app.get("/api/resources/{resource_id}/content")
def resource_content(resource_id: str, user_id: str = Depends(current_user)):
    item = storage.get_resource(user_id, resource_id)
    path = storage.resource_path(user_id, resource_id)
    if not item or not path or not path.is_file():
        raise HTTPException(404, "资源不存在")
    return FileResponse(path, media_type=item["content_type"], filename=item["original_name"])


@app.get("/api/skills")
def list_skills(user_id: str = Depends(current_user)):
    return {"items": storage.list_skills(user_id)}


@app.post("/api/skills", status_code=201)
async def upload_skill(name: str = Query(..., min_length=1, max_length=200), description: str = Query(""), is_public: bool = Query(False), file: Optional[UploadFile] = File(None), user_id: str = Depends(current_user)):
    data = await file.read() if file else b""
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, "文件超过大小限制")
    return storage.save_skill(user_id, name, description, file.filename if file else None, file.content_type if file else None, data, is_public)


@app.get("/api/skills/{skill_id}")
def get_skill(skill_id: str, user_id: str = Depends(current_user)):
    item = storage.get_skill(user_id, skill_id)
    if not item:
        raise HTTPException(404, "skill 不存在")
    return item


@app.put("/api/skills/{skill_id}")
def update_skill(skill_id: str, payload: UpdateModel, user_id: str = Depends(current_user)):
    item = storage.update_skill(user_id, skill_id, payload.model_dump(exclude_none=True))
    if not item:
        raise HTTPException(404, "skill 不存在")
    return item


@app.delete("/api/skills/{skill_id}", status_code=204)
def delete_skill(skill_id: str, user_id: str = Depends(current_user)):
    if not storage.delete_skill(user_id, skill_id):
        raise HTTPException(404, "skill 不存在")


@app.get("/api/skills/{skill_id}/content")
def skill_content(skill_id: str, user_id: str = Depends(current_user)):
    item = storage.get_skill(user_id, skill_id)
    path = storage.skill_path(user_id, skill_id)
    if not item or not path or not path.is_file():
        raise HTTPException(404, "skill 文件不存在")
    return FileResponse(path, media_type=item["content_type"], filename=item["file_name"])


if settings.serve_frontend:
    from fastapi.staticfiles import StaticFiles

    frontend = Path(__file__).parent.parent / "front"
    if frontend.is_dir():
        app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")
