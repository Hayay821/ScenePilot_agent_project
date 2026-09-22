import mimetypes
import re
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


USER_ID_RE = re.compile(r"^[^\\/\x00]{1,128}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Storage:
    """SQLite metadata plus per-user files, with all ownership checks centralized."""

    def __init__(self, root: Path):
        self.root = root
        self.db_path = root / "metadata.sqlite3"
        self._lock = threading.RLock()
        self.root.mkdir(parents=True, exist_ok=True)
        self._db().close()

    def _db(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            """CREATE TABLE IF NOT EXISTS resources (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL, kind TEXT NOT NULL,
                original_name TEXT NOT NULL, stored_name TEXT NOT NULL,
                content_type TEXT, size INTEGER NOT NULL, description TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                UNIQUE(user_id, stored_name)
            )"""
        )
        connection.execute(
            """CREATE TABLE IF NOT EXISTS skills (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL, name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '', file_name TEXT, file_path TEXT,
                content_type TEXT, size INTEGER NOT NULL DEFAULT 0,
                is_public INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            )"""
        )
        connection.commit()
        return connection

    @staticmethod
    def user_dir(root: Path, user_id: str) -> Path:
        if not USER_ID_RE.fullmatch(user_id) or user_id in {".", ".."}:
            raise ValueError("invalid user id for filesystem path")
        return root / "users" / user_id

    def _user_dir(self, user_id: str, category: str) -> Path:
        path = self.user_dir(self.root, user_id) / category
        path.mkdir(parents=True, exist_ok=True)
        return path

    def ensure_user(self, user_id: str) -> Path:
        user_path = self.user_dir(self.root, user_id)
        (user_path / "media").mkdir(parents=True, exist_ok=True)
        (user_path / "skills").mkdir(parents=True, exist_ok=True)
        return user_path

    def save_resource(self, user_id: str, kind: str, original_name: str, content_type: Optional[str], data: bytes, description: str = "") -> Dict[str, Any]:
        original_name = self._file_name(original_name)
        if self._resource_name_exists(user_id, original_name):
            raise FileExistsError("同一用户下已存在同名文件")
        resource_id = str(uuid.uuid4())
        suffix = Path(original_name).suffix.lower()[:20]
        stored_name = resource_id + suffix
        target = self._user_dir(user_id, "media") / stored_name
        target.write_bytes(data)
        now = utc_now()
        with self._lock:
            db = self._db()
            db.execute("INSERT INTO resources VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (resource_id, user_id, kind, original_name, stored_name, content_type or mimetypes.guess_type(original_name)[0], len(data), description, now, now))
            db.commit()
            db.close()
        return self.get_resource(user_id, resource_id)

    def list_resources(self, user_id: str, kind: Optional[str] = None) -> List[Dict[str, Any]]:
        db = self._db()
        if kind:
            rows = db.execute("SELECT * FROM resources WHERE user_id = ? AND kind = ? ORDER BY created_at DESC", (user_id, kind)).fetchall()
        else:
            rows = db.execute("SELECT * FROM resources WHERE user_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()
        db.close()
        return [self._resource_dict(row) for row in rows]

    def get_resource(self, user_id: str, resource_id: str) -> Optional[Dict[str, Any]]:
        db = self._db()
        row = db.execute("SELECT * FROM resources WHERE id = ? AND user_id = ?", (resource_id, user_id)).fetchone()
        db.close()
        return self._resource_dict(row) if row else None

    def update_resource(self, user_id: str, resource_id: str, values: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        allowed = {key: values[key] for key in ("original_name", "description") if key in values}
        if "original_name" in allowed:
            new_name = self._file_name(allowed["original_name"])
            current = self.get_resource(user_id, resource_id)
            if not current:
                return None
            if new_name != current["original_name"] and self._resource_name_exists(user_id, new_name, resource_id):
                raise FileExistsError("同一用户下已存在同名文件")
            old_path = self._user_dir(user_id, "media") / current["stored_name"]
            new_path = self._user_dir(user_id, "media") / new_name
            if new_path.exists() and new_path != old_path:
                raise FileExistsError("目标文件已存在")
            if new_name != current["original_name"]:
                old_path.rename(new_path)
                allowed["original_name"] = new_name
                allowed["stored_name"] = new_name
        if not allowed:
            return self.get_resource(user_id, resource_id)
        allowed["updated_at"] = utc_now()
        assignments = ", ".join(f"{key} = ?" for key in allowed)
        with self._lock:
            db = self._db()
            result = db.execute(f"UPDATE resources SET {assignments} WHERE id = ? AND user_id = ?", (*allowed.values(), resource_id, user_id))
            db.commit()
            db.close()
        return self.get_resource(user_id, resource_id) if result.rowcount else None

    def delete_resource(self, user_id: str, resource_id: str) -> bool:
        resource = self.get_resource(user_id, resource_id)
        if not resource:
            return False
        path = self._user_dir(user_id, "media") / resource["stored_name"]
        with self._lock:
            db = self._db()
            db.execute("DELETE FROM resources WHERE id = ? AND user_id = ?", (resource_id, user_id))
            db.commit()
            db.close()
        path.unlink(missing_ok=True)
        return True

    def resource_path(self, user_id: str, resource_id: str) -> Optional[Path]:
        item = self.get_resource(user_id, resource_id)
        return self._user_dir(user_id, "media") / item["stored_name"] if item else None

    def _resource_name_exists(self, user_id: str, name: str, exclude_id: Optional[str] = None) -> bool:
        db = self._db()
        if exclude_id:
            row = db.execute("SELECT 1 FROM resources WHERE user_id = ? AND original_name = ? AND id != ?", (user_id, name, exclude_id)).fetchone()
        else:
            row = db.execute("SELECT 1 FROM resources WHERE user_id = ? AND original_name = ?", (user_id, name)).fetchone()
        db.close()
        return row is not None

    @staticmethod
    def _file_name(name: str) -> str:
        value = Path(name or "").name.strip()
        if not value or value in {".", ".."} or "\x00" in value:
            raise ValueError("invalid file name")
        return value

    def save_skill(self, user_id: str, name: str, description: str, original_name: Optional[str], content_type: Optional[str], data: bytes, is_public: bool = False) -> Dict[str, Any]:
        skill_id = str(uuid.uuid4())
        stored_name = None
        if original_name:
            stored_name = skill_id + Path(original_name).suffix.lower()[:20]
            (self._user_dir(user_id, "skills") / stored_name).write_bytes(data)
        now = utc_now()
        with self._lock:
            db = self._db()
            db.execute("INSERT INTO skills VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (skill_id, user_id, name, description, original_name, stored_name, content_type, len(data), int(is_public), now, now,))
            db.commit()
            db.close()
        return self.get_skill(user_id, skill_id)

    def list_skills(self, user_id: str) -> List[Dict[str, Any]]:
        db = self._db()
        rows = db.execute("SELECT * FROM skills WHERE user_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()
        db.close()
        return [self._skill_dict(row) for row in rows]

    def get_skill(self, user_id: str, skill_id: str) -> Optional[Dict[str, Any]]:
        db = self._db()
        row = db.execute("SELECT * FROM skills WHERE id = ? AND user_id = ?", (skill_id, user_id)).fetchone()
        db.close()
        return self._skill_dict(row) if row else None

    def update_skill(self, user_id: str, skill_id: str, values: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        allowed = {key: values[key] for key in ("name", "description", "is_public") if key in values}
        if "is_public" in allowed:
            allowed["is_public"] = int(bool(allowed["is_public"]))
        if not allowed:
            return self.get_skill(user_id, skill_id)
        allowed["updated_at"] = utc_now()
        assignments = ", ".join(f"{key} = ?" for key in allowed)
        with self._lock:
            db = self._db()
            result = db.execute(f"UPDATE skills SET {assignments} WHERE id = ? AND user_id = ?", (*allowed.values(), skill_id, user_id))
            db.commit()
            db.close()
        return self.get_skill(user_id, skill_id) if result.rowcount else None

    def delete_skill(self, user_id: str, skill_id: str) -> bool:
        skill = self.get_skill(user_id, skill_id)
        if not skill:
            return False
        if skill["file_path"]:
            (self._user_dir(user_id, "skills") / skill["file_path"]).unlink(missing_ok=True)
        with self._lock:
            db = self._db()
            db.execute("DELETE FROM skills WHERE id = ? AND user_id = ?", (skill_id, user_id))
            db.commit()
            db.close()
        return True

    def skill_path(self, user_id: str, skill_id: str) -> Optional[Path]:
        item = self.get_skill(user_id, skill_id)
        return self._user_dir(user_id, "skills") / item["file_path"] if item and item["file_path"] else None

    @staticmethod
    def _resource_dict(row: sqlite3.Row) -> Dict[str, Any]:
        return dict(row) if row else {}

    @staticmethod
    def _skill_dict(row: sqlite3.Row) -> Dict[str, Any]:
        value = dict(row) if row else {}
        if value:
            value["is_public"] = bool(value["is_public"])
        return value
