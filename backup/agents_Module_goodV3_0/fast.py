"""ScenePilot Fast: a small, media-first four-agent prototype.

The module intentionally keeps the runtime surface small. Skills are English YAML,
user interaction can be Chinese, and every agent returns JSON-serializable data.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import yaml
from dotenv import load_dotenv

from agents.skills_manager_agent import SkillManager, SkillsManagerAgent
from agents.director_agent import DirectorAgent
from agents.cinematographer_agent import CinematographerAgent
from agents.editor_agent import EditorAgent
from editor_workspace import EditorWorkspace
from cinematographer_session import CinematographerSessionStore
from api.schemas import (
    APIErrorEnvelope,
    APIEnvelope,
    CaptureWebcamRequest,
    CinematographerRequest,
    CreateSkillRequest,
    DirectorRequest,
    EditorRequest,
    EditorWorkspaceRequest,
    CinematographerFrameRequest,
    CinematographerSessionStartRequest,
    CinematographerSessionStopRequest,
    ExtractFramesRequest,
    MediaInput,
    MediaSourceType,
    RunAllRequest,
    SelectSkillsRequest,
    SkillsFilter,
)

ROOT = Path(__file__).resolve().parent
SKILLS_DIR = ROOT / "skills" / "repository"
MEDIA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"
MODEL_CACHE_DIR = Path(os.getenv("SCENEPILOT_MODEL_CACHE", "F:/BoldMaker/models/scenepilot_cache"))

# Load .env file
load_dotenv(ROOT / ".env")

# Windows consoles may use GBK; agent progress messages contain non-ASCII text.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _envelope(data: Any, agent_type: str | None = None) -> dict:
    return {"success": True, "data": _json(data), "agent_type": agent_type, "timestamp": _timestamp()}


def _media_paths(media_input: MediaInput | None, default_dir: str | None = None) -> tuple[list[str], list[str]]:
    if media_input is None:
        root = default_dir or str(MEDIA_DIR)
        return MediaTools.images(root), MediaTools.videos(root)
    if media_input.source_type == MediaSourceType.FILE:
        paths = [str(Path(p)) for p in (media_input.paths or [])]
        missing = [p for p in paths if not Path(p).exists()]
        if missing:
            raise FileNotFoundError(f"Media files not found: {missing}")
        images = [p for p in paths if Path(p).suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]
        videos = [p for p in paths if Path(p).suffix.lower() in {".mp4", ".mov", ".avi", ".mkv", ".insv"}]
        return images, videos
    config = media_input.camera_config
    frames = MediaTools.capture_webcam_frames(config.camera_id, 5, config.frame_interval, OUTPUT_DIR / "captures", tuple(config.resolution) if config.resolution else None)
    return frames, []


def _json(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {k: _json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json(v) for v in value]
    return value


class MediaTools:
    """Small local image/video adapter. No camera SDK is required."""

    @staticmethod
    def images(directory: str | Path) -> list[str]:
        root = Path(directory)
        return [str(p) for p in sorted(root.glob("**/*")) if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]

    @staticmethod
    def videos(directory: str | Path) -> list[str]:
        root = Path(directory)
        return [str(p) for p in sorted(root.glob("**/*")) if p.suffix.lower() in {".mp4", ".mov", ".avi", ".mkv", ".insv"}]

    @staticmethod
    def extract_frames(video: str | Path, output: str | Path, every_seconds: float = 2.0, max_frames: int = 12) -> list[str]:
        output = Path(output)
        output.mkdir(parents=True, exist_ok=True)
        cap = cv2.VideoCapture(str(video))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        step = max(1, int(fps * every_seconds))
        paths, index = [], 0
        while len(paths) < max_frames:
            ok, frame = cap.read()
            if not ok:
                break
            if index % step == 0:
                path = output / f"frame_{index:06d}.jpg"
                cv2.imwrite(str(path), frame)
                paths.append(str(path))
            index += 1
        cap.release()
        return paths

    @staticmethod
    def inspect(path: str | Path) -> dict:
        path = Path(path)
        if path.is_dir():
            return {"path": str(path), "type": "directory", "images": MediaTools.images(path), "videos": MediaTools.videos(path)}
        if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
            image = cv2.imread(str(path))
            height, width = image.shape[:2]
            return {"path": str(path), "type": "image", "width": width, "height": height}
        cap = cv2.VideoCapture(str(path))
        result = {"path": str(path), "type": "video", "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), "fps": cap.get(cv2.CAP_PROP_FPS), "frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT))}
        cap.release()
        return result

    @staticmethod
    def rough_cut(video: str | Path, output: str | Path, start: float = 0, duration: float = 10) -> str:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-y", "-ss", str(start), "-i", str(video), "-t", str(duration), "-c", "copy", str(output)], check=True, capture_output=True)
        return str(output)

    @staticmethod
    def capture_webcam_frames(
        camera_id: int,
        num_frames: int,
        interval: float,
        output_dir: str | Path,
        resolution: tuple[int, int] | None = None
    ) -> list[str]:
        """从摄像头捕获多帧图像

        Args:
            camera_id: 摄像头 ID
            num_frames: 捕获帧数
            interval: 捕获间隔（秒）
            output_dir: 输出目录
            resolution: 分辨率 (width, height)

        Returns:
            捕获的图像路径列表
        """
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        cap = cv2.VideoCapture(camera_id)

        if resolution:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

        if not cap.isOpened():
            raise ValueError(f"无法打开摄像头 {camera_id}")

        paths = []
        import time
        for i in range(num_frames):
            ok, frame = cap.read()
            if not ok:
                break
            path = output / f"webcam_{camera_id}_frame_{i}.jpg"
            cv2.imwrite(str(path), frame)
            paths.append(str(path))
            if i < num_frames - 1:
                time.sleep(interval)

        cap.release()
        return paths

    @staticmethod
    def get_available_cameras(max_test: int = 5) -> list[int]:
        """检测可用的摄像头 ID

        Args:
            max_test: 最大测试摄像头数量

        Returns:
            可用摄像头 ID 列表
        """
        available = []
        for i in range(max_test):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(i)
                cap.release()
        return available

    @staticmethod
    def test_camera(camera_id: int) -> dict:
        """测试摄像头是否可用并返回基本信息

        Args:
            camera_id: 摄像头 ID

        Returns:
            摄像头信息字典
        """
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            return {"available": False, "camera_id": camera_id}

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()

        return {
            "available": True,
            "camera_id": camera_id,
            "width": width,
            "height": height,
            "fps": fps
        }


class Provider:
    """Vision provider supporting both mock and real Bailian Qwen-VL API."""

    def __init__(self, mode: str = "mock", model: str | None = None, agent_type: str | None = None):
        self.mode = mode
        self.model = model
        # Support both DASHSCOPE_ and BAILIAN_ prefixes, also check API_KEY
        self.api_key = (
            os.getenv("DASHSCOPE_API_KEY") or
            os.getenv("BAILIAN_API_KEY") or
            os.getenv("API_KEY")
        )
        # Strip whitespace to prevent HTTP header errors
        if self.api_key:
            self.api_key = self.api_key.strip()
        self.base_url = (
            os.getenv("DASHSCOPE_BASE_URL") or
            os.getenv("BAILIAN_BASE_URL") or
            os.getenv("API_URL") or
            "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

        # Select model based on agent type if not explicitly provided
        if not self.model and agent_type:
            # Agent-specific model selection
            agent_model_map = {
                "skills": os.getenv("SKILLS_MODEL") or "qwen-turbo",
                "director": os.getenv("DIRECTOR_MODEL") or "qwen-vl-plus",
                "cinematographer": os.getenv("CINEMATOGRAPHER_MODEL") or "qwen-vl-plus",
                "editor": os.getenv("EDITOR_MODEL") or "qwen-vl-plus",
            }
            self.model = agent_model_map.get(agent_type)

        # Fallback to default model
        if not self.model:
            self.model = (
                os.getenv("DASHSCOPE_MODEL") or
                os.getenv("BAILIAN_MODEL") or
                os.getenv("MODEL") or
                "qwen-vl-plus"
            )

        if self.mode == "bailian" and not self.api_key:
            raise ValueError(
                "Bailian mode requires API key. Please set DASHSCOPE_API_KEY, "
                "BAILIAN_API_KEY, or API_KEY in .env file or environment."
            )

    def _cache_path(self, kind: str, prompt: str, media: list[str] | None = None) -> Path:
        payload = [kind, self.model, self.base_url, prompt]
        for path in media or []:
            p = Path(path)
            stat = p.stat()
            payload.append(f"{p.resolve()}:{stat.st_size}:{stat.st_mtime_ns}")
        digest = hashlib.sha256("\n".join(payload).encode("utf-8")).hexdigest()
        path = MODEL_CACHE_DIR / self.model / f"{digest}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _cached(self, kind: str, prompt: str, media: list[str] | None = None) -> dict | None:
        if self.mode != "bailian" or os.getenv("SCENEPILOT_DISABLE_CACHE") == "1":
            return None
        path = self._cache_path(kind, prompt, media)
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                path.unlink(missing_ok=True)
        return None

    def _save_cache(self, kind: str, prompt: str, result: dict, media: list[str] | None = None) -> None:
        if self.mode == "bailian" and os.getenv("SCENEPILOT_DISABLE_CACHE") != "1":
            self._cache_path(kind, prompt, media).write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")

    def text(self, prompt: str, expect_json: bool = False) -> dict:
        """Call text-only model (for skills manager).

        Args:
            prompt: Text prompt for the model
            expect_json: Whether to expect JSON response

        Returns:
            Dictionary with analysis results
        """
        if self.mode == "mock":
            return {
                "summary": "Mock text analysis",
                "confidence": 0.75
            }

        cached = self._cached("text", prompt)
        if cached is not None:
            return cached

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key, base_url=self.base_url)

            # Call API with text only
            response = None
            last_error = None
            for attempt in range(2):
                try:
                    response = client.chat.completions.create(model=self.model, messages=[{"role": "user", "content": prompt}], temperature=0.2, timeout=60)
                    break
                except Exception as exc:
                    last_error = exc
                    if attempt == 0:
                        time.sleep(1)
            if response is None:
                raise last_error

            result_text = response.choices[0].message.content

            # Try to extract JSON if expected
            if expect_json:
                result = self._extract_json(result_text)
                self._save_cache("text", prompt, result)
                return result

            result = {
                "summary": result_text,
                "confidence": 0.8
            }
            self._save_cache("text", prompt, result)
            return result

        except Exception as e:
            error_msg = str(e)
            if "api" in error_msg.lower() or "key" in error_msg.lower():
                raise ValueError(f"API authentication failed. Please check DASHSCOPE_API_KEY in .env: {error_msg}")
            elif "model" in error_msg.lower():
                raise ValueError(f"Model '{self.model}' not available. Please check model configuration in .env: {error_msg}")
            else:
                raise ValueError(f"Text API call failed: {error_msg}")

    def vision(self, prompt: str, media: list[str], expect_json: bool = False) -> dict:
        """Call vision model with images.

        Args:
            prompt: Text prompt for the model
            media: List of image paths (max 6 will be used)
            expect_json: Whether to expect JSON response

        Returns:
            Dictionary with analysis results
        """
        if self.mode == "mock":
            return {
                "summary": "Mock analysis: a person is visible; keep the subject clear and leave directional space.",
                "events": ["subject_visible"],
                "confidence": 0.75
            }

        cached = self._cached("vision", prompt, media)
        if cached is not None:
            return cached

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key, base_url=self.base_url)

            # Build content with text and images
            content = [{"type": "text", "text": prompt}]
            for path in media[:6]:  # Limit to 6 images
                encoded = base64.b64encode(Path(path).read_bytes()).decode()
                mime = "image/png" if path.lower().endswith(".png") else "image/jpeg"
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{encoded}"}
                })

            # Call API
            response = None
            last_error = None
            for attempt in range(2):
                try:
                    response = client.chat.completions.create(model=self.model, messages=[{"role": "user", "content": content}], temperature=0.2, timeout=90)
                    break
                except Exception as exc:
                    last_error = exc
                    if attempt == 0:
                        time.sleep(1)
            if response is None:
                raise last_error

            result_text = response.choices[0].message.content

            # Try to extract JSON if expected
            if expect_json:
                result = self._extract_json(result_text)
                self._save_cache("vision", prompt, result, media)
                return result

            result = {
                "summary": result_text,
                "events": [],
                "confidence": 0.8
            }
            self._save_cache("vision", prompt, result, media)
            return result

        except Exception as e:
            error_msg = str(e)
            if "api" in error_msg.lower() or "key" in error_msg.lower():
                raise ValueError(f"API authentication failed. Please check DASHSCOPE_API_KEY in .env: {error_msg}")
            elif "model" in error_msg.lower():
                raise ValueError(f"Model '{self.model}' not available. Please check DASHSCOPE_MODEL in .env: {error_msg}")
            else:
                raise ValueError(f"Vision API call failed: {error_msg}")

    @staticmethod
    def _extract_json(text: str) -> dict:
        """Extract JSON from text, handling markdown code fences."""
        # Try direct JSON parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to extract from markdown code fence
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find any JSON object in the text
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        # Return wrapped text if no JSON found
        return {"summary": text, "confidence": 0.5, "parse_error": True}


class ScenePilotFast:
    def __init__(self, mode: str = "mock", skills_root: Path | None = None):
        skills_root = skills_root or SKILLS_DIR
        self.skills = SkillManager(skills_root)

        # Create separate providers for each agent with their specific models
        self.skills_provider = Provider(mode, agent_type="skills")
        self.director_provider = Provider(mode, agent_type="director")
        self.cinematographer_provider = Provider(mode, agent_type="cinematographer")
        self.editor_provider = Provider(mode, agent_type="editor")

        # Initialize agents with their dedicated providers
        self.manager = SkillsManagerAgent(self.skills, self.skills_provider)
        self.director = DirectorAgent(self.director_provider)
        self.cinematographer = CinematographerAgent(self.cinematographer_provider)
        self.editor = EditorAgent(self.editor_provider)
        self.cinematographer_sessions = CinematographerSessionStore(OUTPUT_DIR / "cinematographer_sessions")

    def run_all(self, user_text: str, media_dir: str | None = None, controls: dict | None = None) -> dict:
        media_dir = media_dir or str(MEDIA_DIR)
        controls = controls or {}
        if controls:
            user_text = f"{user_text}\n用户可编程创作规则：{json.dumps(controls, ensure_ascii=False)}"
        images, videos = MediaTools.images(media_dir), MediaTools.videos(media_dir)

        # Select skills
        selected = []
        for stage in ("director", "cinematographer", "editor"):
            for skill in self.skills.select(user_text, stage):
                if skill.get("id") not in {item.get("id") for item in selected}:
                    selected.append(skill)
        if not selected:
            selected = self.skills.list()[:3]

        # Run Director
        director_skills = [s for s in selected if s.get("stage") == "director"] or selected[:1]
        director_result = self.director.run(user_text, director_skills, images[:6])

        # Save director output
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "director.json").write_text(
            json.dumps(_json(director_result), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        # Run Cinematographer
        frames = []
        if videos:
            video_name = Path(videos[0]).stem
            frames_dir = OUTPUT_DIR / "frames" / video_name
            frames = MediaTools.extract_frames(videos[0], frames_dir)

        cinematographer_skills = [s for s in selected if s.get("stage") == "cinematographer"] or selected[:1]
        filming_result = self.cinematographer.run(
            frames or images[:3],
            cinematographer_skills,
            user_text
        )

        # Save filming output
        (OUTPUT_DIR / "filming.json").write_text(
            json.dumps(_json(filming_result), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        # Run Editor
        editor_skills = [s for s in selected if s.get("stage") == "editor"] or selected[:1]
        editing_result = self.editor.run(videos, images, editor_skills, OUTPUT_DIR)

        # Save editing output
        (OUTPUT_DIR / "edit_plan.json").write_text(
            json.dumps(_json(editing_result), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        # Compile full result
        decision_trace = self._build_decision_trace(user_text, selected, images, videos, director_result, filming_result, editing_result)
        result = {
            "skills": selected,
            "director": director_result,
            "filming": filming_result,
            "editing": editing_result,
            "decision_trace": decision_trace,
            "creative_controls": controls,
        }

        # Save combined run.json
        (OUTPUT_DIR / "run.json").write_text(
            json.dumps(_json(result), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        return result

    @staticmethod
    def _build_decision_trace(user_text, skills, images, videos, director, filming, editing):
        """Create the judge-facing explanation layer for the open director demo."""
        skill_trace = []
        for skill in skills:
            rules = skill.get("rules", [])
            rule_items = []
            for rule in rules[:8]:
                if isinstance(rule, dict):
                    rule_id = rule.get("id")
                    if not rule_id:
                        continue
                    rule_items.append({
                        "rule_id": rule_id,
                        "condition": rule.get("when", {}),
                        "advice": rule.get("advice", rule.get("action", {})),
                        "explanation": rule.get("explanation", ""),
                    })
            skill_trace.append({
                "skill_id": skill.get("id", skill.get("skill_id")),
                "stage": skill.get("stage"),
                "source": skill.get("_path", "local"),
                "rules": rule_items,
            })
        return {
            "user_intent": user_text,
            "input_media": {"images": images, "videos": videos},
            "skill_trace": skill_trace,
            "agent_decisions": [
                {
                    "agent": "director",
                    "summary": director.get("user_summary_zh", ""),
                    "evidence": director.get("reference_analysis", []),
                    "output": director.get("shot_plan", []),
                },
                {
                    "agent": "cinematographer",
                    "summary": filming.get("user_summary_zh", ""),
                    "evidence": filming.get("source_frames", []),
                    "output": filming.get("suggestion", {}),
                },
                {
                    "agent": "editor",
                    "summary": editing.get("user_summary_zh", ""),
                    "evidence": editing.get("timeline", []),
                    "output": editing.get("rendered_preview"),
                },
            ],
            "matched_rule_ids": {
                "director": [r.get("id") for s in skills if s.get("stage") == "director" for r in s.get("rules", [])[:3] if r.get("id")],
                "cinematographer": [r.get("id") for s in skills if s.get("stage") == "cinematographer" for r in s.get("rules", [])[:3] if r.get("id")],
                "editor": [r.get("id") for s in skills if s.get("stage") == "editor" for r in s.get("rules", [])[:3] if r.get("id")],
            },
            "editable_controls": [
                "selected_skills",
                "shot_plan",
                "composition",
                "camera_role",
                "timeline_order",
                "output_ratio",
            ],
            "principle": "AI explains and proposes; the user remains the director.",
        }


def build_api(app: ScenePilotFast):
    from fastapi import FastAPI
    from fastapi import HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import RedirectResponse
    api = FastAPI(title="ScenePilot Fast", version="1.0.0")
    api.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    router = api.router

    @api.get("/", include_in_schema=False)
    def root():
        return RedirectResponse(url="/docs")

    @api.get("/health")
    @api.get("/api/v1/health")
    def health():
        return _envelope({"ok": True, "mode": app.director.provider.mode})

    @api.get("/api/v1/media/info")
    def media_info(path: str):
        try:
            return _envelope(MediaTools.inspect(path))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @api.get("/api/v1/media/list")
    def media_list(directory: str = str(MEDIA_DIR), type: str = "all"):
        images = MediaTools.images(directory) if type in ("all", "images") else []
        videos = MediaTools.videos(directory) if type in ("all", "videos") else []
        return _envelope({"images": images, "videos": videos, "total": len(images) + len(videos)})

    @api.post("/api/v1/media/extract-frames")
    def extract_frames(req: ExtractFramesRequest):
        if not Path(req.video_path).exists():
            raise HTTPException(status_code=404, detail="video file not found")
        frames = MediaTools.extract_frames(req.video_path, req.output_dir, req.every_seconds, req.max_frames)
        return _envelope({"frames": frames, "total": len(frames)})

    @api.post("/api/v1/media/capture-webcam")
    def capture_webcam(req: CaptureWebcamRequest):
        try:
            frames = MediaTools.capture_webcam_frames(req.camera_id, req.num_frames, req.interval, req.output_dir, tuple(req.resolution) if req.resolution else None)
            return _envelope({"frames": frames, "camera_id": req.camera_id, "total": len(frames)})
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @api.get("/api/v1/skills")
    def list_skills(stage: str | None = None, limit: int = 20):
        skills = app.skills.list()
        if stage:
            skills = [s for s in skills if s.get("stage") == stage or stage in s.get("stages", [])]
        items = [{"id": s.get("id", s.get("skill_id")), "name": s.get("name_en", s.get("name", "")), "description": s.get("description", ""), "stage": s.get("stage", ""), "tags": s.get("tags", []), "path": s.get("_path", "")} for s in skills[:limit]]
        return _envelope({"skills": items, "total": len(items)})

    @api.get("/api/v1/skills/{skill_id}")
    def skill_detail(skill_id: str):
        skill = next((s for s in app.skills.list() if s.get("id") == skill_id or s.get("skill_id") == skill_id), None)
        if not skill:
            raise HTTPException(status_code=404, detail="skill not found")
        return _envelope(skill)

    @api.post("/api/v1/skills/select")
    def select_skills(req: SelectSkillsRequest):
        skills = app.skills.select(req.user_text, req.stage)[:req.limit or 3]
        items = [{"id": s.get("id", s.get("skill_id")), "name": s.get("name_en", s.get("name", "")), "relevance_score": 1.0} for s in skills]
        return _envelope({"skills": items, "total": len(items)}, "skills_manager")

    @api.post("/api/v1/skills/interact")
    def skills_interact(req: SelectSkillsRequest):
        return _envelope(app.manager.interact(req.user_text, req.stage or "director"), "skills_manager")

    @api.post("/api/v1/agents/director")
    def director(req: DirectorRequest):
        images, _ = _media_paths(req.media_input)
        skills = app.skills.select(req.user_text, "director")[:req.skills_filter.limit if req.skills_filter and req.skills_filter.limit else 3]
        return _envelope(app.director.run(req.user_text, skills, images), "director")

    @api.post("/api/v1/agents/cinematographer")
    def cinematographer(req: CinematographerRequest):
        images, videos = _media_paths(req.media_input)
        frames = images
        if videos:
            frames = MediaTools.extract_frames(videos[0], OUTPUT_DIR / "frames" / Path(videos[0]).stem)
        skills = app.skills.select(req.user_text, "cinematographer")[:req.skills_filter.limit if req.skills_filter and req.skills_filter.limit else 3]
        return _envelope(app.cinematographer.run(frames, skills, req.user_text), "cinematographer")

    @api.post("/api/v1/agents/cinematographer/session/start")
    def start_cinematographer_session(req: CinematographerSessionStartRequest):
        skills = app.skills.select(req.user_text, "cinematographer")[:req.skills_filter.limit if req.skills_filter and req.skills_filter.limit else 3]
        session = app.cinematographer_sessions.start(req.user_text, skills, app.cinematographer_provider, OUTPUT_DIR / "cinematographer_sessions")
        stream = app.cinematographer_sessions.add_stream(
            session["session_id"], req.stream_id, req.source_type, req.device_id
        )
        return _envelope({
            "session_id": session["session_id"],
            "active": True,
            "interval_ms": 500,
            "streams": [stream],
            "matched_skills": [s.get("id") for s in skills],
            "skills_guidance": app.skills.explain(skills),
            "message_zh": "拍摄会话已启动，首次帧分析会携带用户要求和 Skill；后续帧使用服务端会话记忆。",
        }, "cinematographer")

    @api.post("/api/v1/agents/cinematographer/session/{session_id}/streams")
    def register_cinematographer_stream(session_id: str, req: CinematographerSessionStartRequest):
        stream = app.cinematographer_sessions.add_stream(
            session_id, req.stream_id, req.source_type, req.device_id
        )
        return _envelope(stream, "cinematographer")

    @api.post("/api/v1/agents/cinematographer/session/{session_id}/frame")
    def analyze_cinematographer_frame(session_id: str, req: CinematographerFrameRequest):
        result = app.cinematographer_sessions.analyze_frame(
            session_id,
            req.frame_data,
            req.stream_id,
            req.timestamp_ms,
            req.sequence,
        )
        return _envelope(result, "cinematographer")

    @api.post("/api/v1/agents/cinematographer/session/{session_id}/stop")
    def stop_cinematographer_session(session_id: str):
        return _envelope(app.cinematographer_sessions.stop(session_id), "cinematographer")

    @api.post("/api/v1/agents/editor")
    def editor(req: EditorRequest):
        images, videos = _media_paths(req.media_input)
        skills = app.skills.select(req.user_text, "editor")[:req.skills_filter.limit if req.skills_filter and req.skills_filter.limit else 3]
        result = app.editor.run(videos, images, skills, Path(req.output_config.output_dir) if req.output_config and req.output_config.output_dir else OUTPUT_DIR)
        return _envelope(result, "editor")

    @api.post("/api/v1/editor/workspace")
    def editor_workspace(req: EditorWorkspaceRequest):
        payload = req
        workspace = EditorWorkspace(payload.workspace_dir or str(OUTPUT_DIR / "editor_workspace"))
        result = workspace.build(
            payload.v1_path,
            payload.v2_path,
            payload.prompt,
            payload.reference_frame,
            payload.use_ai_transition,
        )
        return _envelope(result, "editor")

    @api.get("/api/v1/editor/workspace/{workspace_id}")
    def editor_workspace_result(workspace_id: str):
        root = OUTPUT_DIR / "editor_workspace"
        matches = list(root.rglob(f"{workspace_id}.json"))
        if not matches:
            raise HTTPException(status_code=404, detail="workspace result not found")
        return _envelope(json.loads(matches[0].read_text(encoding="utf-8")), "editor")

    @api.post("/api/v1/agents/run-all")
    def run_all(req: RunAllRequest):
        result = app.run_all(req.user_text, req.media_dir, req.controls)
        return _envelope(result)

    @api.get("/api/v1/demo/decision-trace")
    def decision_trace():
        trace_path = OUTPUT_DIR / "run.json"
        if not trace_path.exists():
            raise HTTPException(status_code=404, detail="run.json not found; run the workflow first")
        payload = json.loads(trace_path.read_text(encoding="utf-8"))
        return _envelope(payload.get("decision_trace", {}), "scene_pilot")

    # Keep the short legacy routes used by the initial frontend prototype.
    @api.post("/skills/interact")
    def legacy_skills(req: SelectSkillsRequest): return skills_interact(req)
    @api.post("/director")
    def legacy_director(req: DirectorRequest): return director(req)
    @api.post("/cinematographer")
    def legacy_cinematographer(req: CinematographerRequest): return cinematographer(req)
    @api.post("/editor")
    def legacy_editor(req: EditorRequest): return editor(req)
    @api.post("/run")
    def legacy_run(req: RunAllRequest): return run_all(req)

    return api


def main() -> None:
    parser = argparse.ArgumentParser(description="ScenePilot Fast")
    parser.add_argument("command", choices=["run", "skills", "frames", "inspect", "serve"])
    parser.add_argument("--text", default="Create a natural portrait video")
    parser.add_argument("--media", default=str(MEDIA_DIR))
    parser.add_argument("--video")
    parser.add_argument("--mode", choices=["mock", "bailian"], default="mock")
    args = parser.parse_args()
    app = ScenePilotFast(args.mode)
    if args.command == "skills": print(json.dumps(app.manager.interact(args.text, "director"), ensure_ascii=False, indent=2))
    elif args.command == "run": print(json.dumps(_json(app.run_all(args.text, args.media)), ensure_ascii=False, indent=2))
    elif args.command == "inspect": print(json.dumps(MediaTools.inspect(args.media), ensure_ascii=False, indent=2))
    elif args.command == "frames": print(json.dumps(MediaTools.extract_frames(args.video, OUTPUT_DIR / "frames"), ensure_ascii=False, indent=2))
    elif args.command == "serve":
        import uvicorn
        uvicorn.run(build_api(app), host="127.0.0.1", port=8765)


if __name__ == "__main__": main()
