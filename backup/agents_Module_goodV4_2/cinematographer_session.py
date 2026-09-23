"""Stateful cinematographer sessions for browser/webcam frame analysis.

The model API is stateless. Memory is kept locally by this service and a compact
summary is sent with every frame request. Skills are sent only on session start.
"""
from __future__ import annotations

import base64
import json
import threading
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
            "source_type": "browser_test",
            "streams": {},
            "lock": threading.RLock(),
            "active": True,
        }
        Path(session["output_dir"]).mkdir(parents=True, exist_ok=True)
        self.sessions[session_id] = session
        return session

    def add_stream(self, session_id: str, stream_id: str, source_type: str, device_id: str | None = None) -> dict:
        session = self.sessions.get(session_id)
        if not session or not session["active"]:
            raise ValueError("cinematographer session is not active")
        with session["lock"]:
            stream = session["streams"].setdefault(stream_id, {
                "stream_id": stream_id,
                "source_type": source_type,
                "device_id": device_id,
                "frame_count": 0,
                "captures": [],
                "memory": [],
                "last_sequence": None,
                "last_timestamp_ms": None,
                "in_flight": False,
            })
            stream["source_type"] = source_type
            stream["device_id"] = device_id
            return {k: v for k, v in stream.items() if k not in {"memory", "captures"}}

    @staticmethod
    def decode_frame(data: str, output: Path) -> str:
        if "," in data:
            data = data.split(",", 1)[1]
        output.write_bytes(base64.b64decode(data))
        return str(output)

    def analyze_frame(
        self,
        session_id: str,
        frame_data: str,
        stream_id: str = "browser_main",
        timestamp_ms: int | None = None,
        sequence: int | None = None,
    ) -> dict:
        session = self.sessions.get(session_id)
        if not session or not session["active"]:
            raise ValueError("cinematographer session is not active")

        with session["lock"]:
            if stream_id not in session["streams"]:
                self.add_stream(session_id, stream_id, session.get("source_type", "external"))
            stream = session["streams"][stream_id]
            if stream["in_flight"]:
                return {"session_id": session_id, "stream_id": stream_id, "skipped": True, "reason": "previous_frame_still_processing"}
            stream["in_flight"] = True
            index = stream["frame_count"]

        try:
            stream_dir = Path(session["output_dir"]) / "streams" / stream_id
            frame_path = stream_dir / "frames" / f"frame_{index:06d}.jpg"
            frame_path.parent.mkdir(parents=True, exist_ok=True)
            self.decode_frame(frame_data, frame_path)

            # Each stream has isolated short memory; the model itself is stateless.
            memory = stream["memory"][-3:]
            timestamp_ms = timestamp_ms if timestamp_ms is not None else index * 500
            sequence = sequence if sequence is not None else index
            prompt = f"""你是实时人像摄影指导。用户目标：{session['user_text']}
这是视频流 {stream_id} 的当前帧，时间戳 {timestamp_ms} ms，序号 {sequence}。服务端记忆摘要：{json.dumps(memory, ensure_ascii=False)}
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
                capture = stream_dir / "captures" / f"capture_{index:06d}.jpg"
                capture.parent.mkdir(exist_ok=True)
                capture.write_bytes(frame_path.read_bytes())
                captured = str(capture)
                stream["captures"].append(captured)

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
                "stream_id": stream_id,
                "timestamp_ms": timestamp_ms,
                "sequence": sequence,
            }
            stream["memory"].append({
                "frame_index": index,
                "timestamp_ms": timestamp_ms,
                "action": action,
                "summary": result.get("summary", ""),
                "confidence": confidence,
            })
            stream["frame_count"] += 1
            stream["last_sequence"] = sequence
            stream["last_timestamp_ms"] = timestamp_ms
            return summary
        finally:
            stream["in_flight"] = False

    def stop(self, session_id: str) -> dict:
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError("session not found")
        session["active"] = False
        streams = {
            stream_id: {
                "source_type": stream["source_type"],
                "device_id": stream["device_id"],
                "frame_count": stream["frame_count"],
                "captures": stream["captures"],
                "last_sequence": stream["last_sequence"],
                "last_timestamp_ms": stream["last_timestamp_ms"],
            }
            for stream_id, stream in session["streams"].items()
        }
        result = {
            "session_id": session_id,
            "active": False,
            "streams": streams,
            "frame_count": sum(stream["frame_count"] for stream in session["streams"].values()),
            "captures": [path for stream in session["streams"].values() for path in stream["captures"]],
            "output_dir": session["output_dir"],
        }
        Path(session["output_dir"]).joinpath("session.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return result
