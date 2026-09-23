"""Cinematographer Agent: real-time shooting guidance based on camera frames."""
from __future__ import annotations

from pathlib import Path
from typing import Any


class CinematographerAgent:
    """Analyzes camera frames and provides real-time shooting suggestions."""

    def __init__(self, provider: Any, skills_manager: Any = None):
        self.provider = provider
        self.skills_manager = skills_manager

    def run(self, frame_paths: list[str], skills: list[dict], user_text: str = "") -> dict:
        """Analyze frames and decide whether to capture.

        Args:
            frame_paths: List of extracted frame paths
            skills: Selected skills from SkillsManager
            user_text: User's shooting goal in Chinese

        Returns:
            Dictionary with source_frames, analysis, suggestion, captured_frame, user_summary_zh
        """
        if not frame_paths:
            return {
                "source_frames": [],
                "analysis": {"summary": "No frames to analyze", "confidence": 0.0},
                "suggestion": {"composition": "unknown", "action": "wait_and_recheck", "reason": "No input frames"},
                "captured_frame": None,
                "matched_skills": [],
                "skills_guidance": "",
                "user_summary_zh": "未检测到画面帧，请提供有效的图像或视频帧。"
            }

        # Display Skills matching feedback to user
        print("\n" + "="*60)
        print("📹 Cinematographer Agent - Skills 匹配结果")
        print("="*60)
        print(f"用户意图: {user_text}")
        print(f"\n匹配到 {len(skills)} 个相关 Skills:")
        for idx, skill in enumerate(skills, 1):
            skill_name = skill.get('name', skill.get('id', 'Unknown'))
            skill_desc = skill.get('description', '无描述')
            print(f"  {idx}. {skill_name}")
            print(f"     └─ {skill_desc}")
        print("="*60 + "\n")

        # Build skill context
        skill_context = "\n".join([
            f"- {s.get('name', s.get('id'))}: {s.get('description', '')}"
            for s in skills
        ])

        prompt = f"""你是一位摄影师，正在分析人像拍摄的相机画面帧。

用户目标：{user_text}

相关技能规范（你必须遵循这些规范）：
{skill_context}

分析这些画面帧，然后提供结构化的 JSON 响应：
{{
  "subject_visible": true,
  "face_visible": true,
  "tracking_confidence": 0.87,
  "composition_quality": 0.80,
  "summary": "对画面质量和构图的简要观察（中文）",
  "action_recommendation": "capture_frame 或 wait_and_recheck",
  "composition_suggestion": "medium_portrait（中景人像）、wide_shot（广角）、close_up（特写）等",
  "reason": "为什么拍摄或等待（中文）",
  "skills_guidance": "说明你是如何应用上述 Skills 规范的（中文）",
  "confidence": 0.85
}}

只返回 JSON，不要 markdown 代码块。所有文本内容必须用中文。"""

        print("📸 正在使用视觉模型分析画面帧...")

        try:
            result = self.provider.vision(prompt, frame_paths[:6], expect_json=True)

            # Extract analysis
            analysis = {
                "subject_visible": result.get("subject_visible", True),
                "face_visible": result.get("face_visible", True),
                "tracking_confidence": result.get("tracking_confidence", 0.75),
                "composition_quality": result.get("composition_quality", 0.70),
                "summary": result.get("summary", "Frame analyzed"),
                "confidence": result.get("confidence", 0.75)
            }

            action = result.get("action_recommendation", "capture_frame")
            composition = result.get("composition_suggestion", "medium_portrait")
            reason = result.get("reason", "Frame is suitable for capture")
            skills_guidance = result.get("skills_guidance", "")

            # Display skills guidance to user
            if skills_guidance:
                print(f"\n✨ Skills 应用指导:\n{skills_guidance}\n")

            # Determine if we should capture based on confidence
            if analysis["confidence"] < 0.6 or action == "wait_and_recheck":
                action = "wait_and_recheck"
                captured = None
                user_summary_zh = "当前画面质量不足，建议等待更好的构图。"
            else:
                action = "capture_frame"
                # Capture the best frame (first one for now)
                captured = frame_paths[0]

                # Copy to captures directory
                from fast import OUTPUT_DIR
                captures_dir = OUTPUT_DIR / "captures"
                captures_dir.mkdir(parents=True, exist_ok=True)

                import shutil
                capture_name = Path(frame_paths[0]).name
                capture_path = captures_dir / capture_name
                shutil.copy2(frame_paths[0], capture_path)
                captured = str(capture_path)

                user_summary_zh = "已分析当前画面并标记拍摄建议。"

        except Exception as e:
            import traceback
            print(f"⚠️  视觉分析失败: {e}")
            print(f"完整错误信息:")
            traceback.print_exc()
            analysis = {
                "subject_visible": True,
                "face_visible": False,
                "tracking_confidence": 0.5,
                "composition_quality": 0.5,
                "summary": f"Analysis failed: {str(e)}",
                "confidence": 0.5
            }
            action = "wait_and_recheck"
            composition = "medium_portrait"
            reason = "Unable to analyze frame quality"
            skills_guidance = f"视觉分析失败，使用基础拍摄建议"
            captured = None
            user_summary_zh = f"画面分析失败（{str(e)}），建议重试。"

        # Build source frames metadata
        source_frames = []
        for i, path in enumerate(frame_paths):
            source_frames.append({
                "path": path,
                "index": i,
                "timestamp_ms": i * 2000  # Assuming 2-second intervals
            })

        print(f"✅ Cinematographer 分析完成\n")

        return {
            "source_frames": source_frames,
            "analysis": analysis,
            "suggestion": {
                "action": action,
                "composition": composition,
                "reason": reason
            },
            "captured_frame": captured,
            "matched_skills": [s["id"] for s in skills],
            "skills_guidance": skills_guidance,
            "user_summary_zh": user_summary_zh
        }
