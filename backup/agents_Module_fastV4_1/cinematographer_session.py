"""Stateful cinematographer sessions for browser/webcam frame analysis.

The model API is stateless. Memory is kept locally by this service and a compact
summary is sent with every frame request. Skills are sent only on session start.
"""
from __future__ import annotations

import base64
import json
import time
import uuid
from pathlib import Path


class CinematographerSessionStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.sessions: dict[str, dict] = {}

    def start(self, user_text: str, skills: list[dict], provider, output_root: str | Path) -> dict:
        session_id = f"cam_{uuid.uuid4().hex[:10]}"
        session = {
            "session_id": session_id,
            "user_text": user_text,
            "skills": skills,
            "provider": provider,
            "output_dir": str(Path(output_root) / session_id),
            "started_at": time.time(),
            "frame_count": 0,
            "captures": [],
            "memory": [],
            "active": True,
        }
        Path(session["output_dir"]).mkdir(parents=True, exist_ok=True)
        self.sessions[session_id] = session
        return session

    @staticmethod
    def decode_frame(data: str, output: Path) -> str:
        if "," in data:
            data = data.split(",", 1)[1]
        output.write_bytes(base64.b64decode(data))
        return str(output)

    def analyze_frame(self, session_id: str, frame_data: str) -> dict:
        session = self.sessions.get(session_id)
        if not session or not session["active"]:
            raise ValueError("cinematographer session is not active")

        index = session["frame_count"]
        frame_path = Path(session["output_dir"]) / f"frame_{index:06d}.jpg"
        self.decode_frame(frame_data, frame_path)
        session["frame_count"] += 1

        # The first call established skills and intent. Later calls contain only
        # the current frame plus a short local memory, not the full history.
        memory = session["memory"][-3:]
        prompt = f"""你是实时人像摄影指导。用户目标：{session['user_text']}
这是同一拍摄会话的当前帧。服务端记忆摘要：{json.dumps(memory, ensure_ascii=False)}
只分析当前帧，并返回 JSON：
{{"subject_visible":true,"face_visible":true,"tracking_confidence":0.0,
"composition_quality":0.0,"summary":"中文","action_recommendation":"move_forward|move_backward|move_left|move_right|adjust_angle|capture_frame|wait_and_recheck",
"composition_suggestion":"English short value","reason":"中文","confidence":0.0}}
不要输出 Markdown。当前帧不合格时不要建议 capture_frame。"""
        result = session["provider"].vision(prompt, [str(frame_path)], expect_json=True)
        confidence = float(result.get("confidence", 0.0) or 0.0)
        action = result.get("action_recommendation", "wait_and_recheck")
        if confidence < 0.65:
            action = "wait_and_recheck"
        captured = None
        if action == "capture_frame":
            capture = Path(session["output_dir"]) / "captures" / f"capture_{index:06d}.jpg"
            capture.parent.mkdir(exist_ok=True)
            capture.write_bytes(frame_path.read_bytes())
            captured = str(capture)
            session["captures"].append(captured)

        summary = {
            "frame_index": index,
            "frame_path": str(frame_path),
            "analysis": result,
            "suggestion": {
                "action": action,
                "composition": result.get("composition_suggestion", "unknown"),
                "reason": result.get("reason", "")
            },
            "captured_frame": captured,
            "session_id": session_id,
        }
        session["memory"].append({
            "frame_index": index,
            "action": action,
            "summary": result.get("summary", ""),
            "confidence": confidence,
        })
        return summary

    def stop(self, session_id: str) -> dict:
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError("session not found")
        session["active"] = False
        result = {
            "session_id": session_id,
            "active": False,
            "frame_count": session["frame_count"],
            "captures": session["captures"],
            "output_dir": session["output_dir"],
        }
        Path(session["output_dir"]).joinpath("session.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return result
