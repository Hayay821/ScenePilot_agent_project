"""Editor Agent: editing guidance and execution for video/image composition."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class EditorAgent:
    """Analyzes video/image sources and generates editing plans with preview output."""

    def __init__(self, provider: Any, skills_manager: Any = None):
        self.provider = provider
        self.skills_manager = skills_manager

    def run(
        self,
        video_paths: list[str],
        image_paths: list[str],
        skills: list[dict],
        output_dir: str | Path
    ) -> dict:
        """Generate editing plan and render preview.

        Args:
            video_paths: List of video source paths
            image_paths: List of image source paths
            skills: Selected skills from SkillsManager
            output_dir: Directory for preview output

        Returns:
            Dictionary with timeline, rendered_preview, render info, user_summary_zh
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Display Skills matching feedback to user
        print("\n" + "="*60)
        print("✂️  Editor Agent - Skills 匹配结果")
        print("="*60)
        print(f"匹配到 {len(skills)} 个相关 Skills:")
        for idx, skill in enumerate(skills, 1):
            skill_name = skill.get('name', skill.get('id', 'Unknown'))
            skill_desc = skill.get('description', '无描述')
            print(f"  {idx}. {skill_name}")
            print(f"     └─ {skill_desc}")
        print("="*60 + "\n")

        # Build timeline from all sources
        timeline = []
        for video in video_paths:
            timeline.append({
                "source": video,
                "role": "portrait_source",
                "reason": "主视频素材",
                "keep": True
            })
        for img in image_paths[:3]:  # Limit reference images
            timeline.append({
                "source": img,
                "role": "reference_frame",
                "reason": "参考图片",
                "keep": True
            })

        # If we have videos and images, analyze them with vision model
        analysis_summary = ""
        skills_guidance = ""

        if video_paths or image_paths:
            # Use a few frames/images for analysis
            media_for_analysis = []

            # Extract a few frames from first video if available
            if video_paths:
                from fast import MediaTools, OUTPUT_DIR
                video_name = Path(video_paths[0]).stem
                frames_dir = OUTPUT_DIR / "frames" / video_name
                if frames_dir.exists():
                    # Use already extracted frames
                    media_for_analysis.extend([str(p) for p in sorted(frames_dir.glob("*.jpg"))[:4]])

            # Add reference images
            media_for_analysis.extend(image_paths[:2])

            if media_for_analysis:
                skill_context = "\n".join([
                    f"- {s.get('name', s.get('id'))}: {s.get('description', '')}"
                    for s in skills
                ])

                prompt = f"""你是一位视频剪辑师，正在分析人像视频素材。

相关技能规范（你必须遵循这些规范）：
{skill_context}

分析这些视频帧和图片，然后用 JSON 格式提供剪辑建议：
{{
  "timeline_suggestions": [
    {{"source_type": "video", "role": "establishing_shot", "reason": "建立场景背景"}},
    {{"source_type": "video", "role": "main_portrait", "reason": "主要人物特写"}},
    {{"source_type": "video", "role": "reaction_shot", "reason": "情绪反应镜头"}}
  ],
  "output_format": "9:16 或 16:9",
  "editing_style": "自然、电影感、快节奏等",
  "summary": "简要分析素材质量和剪辑方向（用中文）",
  "skills_guidance": "说明你是如何应用上述 Skills 规范的（中文）",
  "confidence": 0.85
}}

只返回 JSON，不要 markdown 代码块。所有文本内容必须用中文。"""

                print("🎬 正在使用视觉模型分析素材...")

                try:
                    result = self.provider.vision(prompt, media_for_analysis, expect_json=True)
                    analysis_summary = result.get("summary", "已完成素材分析")
                    skills_guidance = result.get("skills_guidance", "")

                    # Display skills guidance to user
                    if skills_guidance:
                        print(f"\n✨ Skills 应用指导:\n{skills_guidance}\n")

                    # Enhance timeline with AI suggestions
                    suggestions = result.get("timeline_suggestions", [])
                    for i, item in enumerate(timeline):
                        if i < len(suggestions):
                            item["ai_role"] = suggestions[i].get("role", item["role"])
                            item["ai_reason"] = suggestions[i].get("reason", item["reason"])

                except Exception as e:
                    import traceback
                    print(f"⚠️  视觉分析失败: {e}")
                    print(f"完整错误信息:")
                    traceback.print_exc()
                    analysis_summary = f"基础剪辑方案（视觉分析失败：{str(e)}）"
                    skills_guidance = "视觉分析失败，使用基础剪辑方案"

        # Generate preview using rough_cut (take first 10 seconds of first video)
        preview_path = None
        if video_paths:
            try:
                from fast import MediaTools
                preview_output = output_dir / "preview.mp4"
                preview_path = MediaTools.rough_cut(
                    video_paths[0],
                    preview_output,
                    start=0,
                    duration=10
                )
                print(f"Generated preview: {preview_path}")
            except Exception as e:
                print(f"Warning: Failed to generate preview: {e}")
                preview_path = None

        # Determine output format based on first video if available
        output_format = "9:16"
        if video_paths:
            try:
                from fast import MediaTools
                info = MediaTools.inspect(video_paths[0])
                width = info.get("width", 720)
                height = info.get("height", 1280)
                if width > height:
                    output_format = "16:9"
            except Exception:
                pass

        user_summary = "已生成剪辑时间线"
        if preview_path:
            user_summary += "和预览视频"
        if analysis_summary:
            user_summary += f"。{analysis_summary}"
        else:
            user_summary += "。"

        print(f"✅ Editor 分析完成\n")

        return {
            "timeline": timeline,
            "rendered_preview": str(preview_path) if preview_path else None,
            "render": {"ratio": output_format, "format": "mp4"},
            "matched_skills": [s["id"] for s in skills],
            "skills_guidance": skills_guidance,
            "analysis_summary": analysis_summary,
            "user_summary_zh": user_summary
        }
