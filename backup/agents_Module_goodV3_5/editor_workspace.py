"""Minimal editor workspace: v1 + AI transition + v2 -> output video."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any

import cv2
import requests


class EditorWorkspace:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.media = self.root / "media"
        self.frames = self.root / "frames"
        self.normalized = self.root / "normalized"
        self.transitions = self.root / "transitions"
        self.renders = self.root / "renders"
        for path in (self.media, self.frames, self.normalized, self.transitions, self.renders):
            path.mkdir(exist_ok=True)

    def manifest(self) -> dict:
        files = []
        for path in sorted(self.root.rglob("*")):
            if path.is_file() and path.name not in {"manifest.json"}:
                files.append({"name": path.name, "path": str(path), "size": path.stat().st_size})
        return {"workspace": str(self.root), "files": files}

    def _last_frame(self, video: str | Path, name: str) -> str:
        cap = cv2.VideoCapture(str(video))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, total - 1))
        ok, frame = cap.read()
        cap.release()
        if not ok:
            raise ValueError(f"Cannot read last frame: {video}")
        output = self.frames / name
        cv2.imwrite(str(output), frame)
        return str(output)

    def _first_frame(self, video: str | Path, name: str) -> str:
        cap = cv2.VideoCapture(str(video))
        ok, frame = cap.read()
        cap.release()
        if not ok:
            raise ValueError(f"Cannot read first frame: {video}")
        output = self.frames / name
        cv2.imwrite(str(output), frame)
        return str(output)

    def _normalize(self, source: str | Path, name: str) -> str:
        output = self.normalized / name
        command = [
            "ffmpeg", "-y", "-i", str(source),
            "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=30",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output),
        ]
        subprocess.run(command, check=True, capture_output=True)
        return str(output)

    def _concat(self, paths: list[str], output: str) -> str:
        list_file = self.renders / f"concat_{uuid.uuid4().hex[:8]}.txt"
        list_file.write_text("\n".join(f"file '{Path(p).resolve().as_posix()}'" for p in paths), encoding="utf-8")
        try:
            subprocess.run([
                "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
                "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", str(output),
            ], check=True, capture_output=True)
        finally:
            list_file.unlink(missing_ok=True)
        return str(output)

    def _video_task(self, first_frame: str, last_frame: str, prompt: str) -> dict:
        """Call a configurable DashScope first/last-frame task endpoint.

        Local paths are converted to data URLs. If a model/account rejects data URLs,
        set DASHSCOPE_FIRST_FRAME_URL and DASHSCOPE_LAST_FRAME_URL to accessible URLs.
        """
        api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("BAILIAN_API_KEY")
        if not api_key:
            raise RuntimeError("DASHSCOPE_API_KEY is not configured")
        endpoint = os.getenv("DASHSCOPE_VIDEO_API_URL", "https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis")
        model = os.getenv("DASHSCOPE_VIDEO_MODEL", "wan2.1-kf2v-plus")

        def image_value(path: str, env_name: str) -> str:
            override = os.getenv(env_name)
            if override:
                return override
            import base64
            encoded = base64.b64encode(Path(path).read_bytes()).decode()
            return f"data:image/jpeg;base64,{encoded}"

        payload = {
            "model": model,
            "input": {
                "first_frame_url": image_value(first_frame, "DASHSCOPE_FIRST_FRAME_URL"),
                "last_frame_url": image_value(last_frame, "DASHSCOPE_LAST_FRAME_URL"),
                "prompt": prompt,
            },
        }
        response = requests.post(endpoint, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        task_id = data.get("output", {}).get("task_id") or data.get("task_id")
        if not task_id:
            raise RuntimeError(f"DashScope did not return task_id: {data}")
        status_url = os.getenv("DASHSCOPE_VIDEO_STATUS_URL", "https://dashscope.aliyuncs.com/api/v1/tasks/") + task_id
        deadline = time.time() + float(os.getenv("DASHSCOPE_VIDEO_TIMEOUT_SEC", "300"))
        while time.time() < deadline:
            status = requests.get(status_url, headers={"Authorization": f"Bearer {api_key}"}, timeout=30)
            status.raise_for_status()
            body = status.json()
            output = body.get("output", {})
            state = output.get("task_status") or body.get("task_status")
            if state in {"SUCCEEDED", "SUCCESS", "succeeded"}:
                url = output.get("video_url") or output.get("url")
                if not url:
                    raise RuntimeError(f"DashScope succeeded without video URL: {body}")
                return {"task_id": task_id, "status": state, "video_url": url}
            if state in {"FAILED", "CANCELED", "failed", "canceled"}:
                raise RuntimeError(f"DashScope task failed: {body}")
            time.sleep(3)
        raise TimeoutError(f"DashScope task timed out: {task_id}")

    def build(self, v1: str, v2: str, prompt: str, reference_frame: str | None = None, use_ai_transition: bool = True) -> dict:
        workspace_id = uuid.uuid4().hex[:8]
        v1 = str(Path(v1)); v2 = str(Path(v2))
        if not Path(v1).exists() or not Path(v2).exists():
            raise FileNotFoundError("v1 and v2 must both exist")
        v1_norm = self._normalize(v1, f"{workspace_id}_v1.mp4")
        v2_norm = self._normalize(v2, f"{workspace_id}_v2.mp4")
        last_frame = self._last_frame(v1_norm, f"{workspace_id}_v1_last.jpg")
        first_frame = self._first_frame(v2_norm, f"{workspace_id}_v2_first.jpg")
        transition = None
        transition_meta: dict[str, Any] = {"used": False, "fallback": None}

        if use_ai_transition:
            try:
                task = self._video_task(first_frame, last_frame, prompt)
                transition = str(self.transitions / f"{workspace_id}_transition.mp4")
                data = requests.get(task["video_url"], timeout=120)
                data.raise_for_status()
                Path(transition).write_bytes(data.content)
                transition_meta = {"used": True, "task_id": task["task_id"], "video_url": task["video_url"]}
            except Exception as exc:
                transition_meta = {"used": False, "fallback": str(exc)}

        pieces = [v1_norm]
        if transition and Path(transition).exists():
            pieces.append(self._normalize(transition, f"{workspace_id}_transition_norm.mp4"))
        pieces.append(v2_norm)
        output = self.renders / f"{workspace_id}_output.mp4"
        self._concat(pieces, str(output))
        result = {
            "workspace_id": workspace_id,
            "workspace": str(self.root),
            "inputs": {"v1": v1, "v2": v2, "reference_frame": reference_frame},
            "frames": {"v1_last": last_frame, "v2_first": first_frame},
            "transition": transition_meta,
            "output_video": str(output),
            "pieces": pieces,
            "prompt": prompt,
        }
        (self.root / f"{workspace_id}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return result
