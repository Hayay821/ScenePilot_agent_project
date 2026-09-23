"""Director Agent: pre-shoot planning based on user needs and reference images."""
from __future__ import annotations

from typing import Any


class DirectorAgent:
    """Analyzes reference images and creates shot plans before filming."""

    def __init__(self, provider: Any):
        self.provider = provider

    def run(self, user_text: str, skills: list[dict], images: list[str] | None = None) -> dict:
        """Generate director plan with optional reference image analysis.

        Args:
            user_text: User's shooting goal in Chinese
            skills: Selected skills from SkillsManager
            images: Optional reference images for analysis

        Returns:
            Dictionary with goal, skills, shot_plan, reference_analysis, user_summary_zh
        """
        reference_analysis = []

        if images:
            # Build skill context for the prompt
            skill_context = "\n".join([
                f"- {s.get('name', s.get('id'))}: {s.get('description', '')}"
                for s in skills
            ])

            prompt = f"""你是一位电影导演，正在分析人像拍摄的参考图片。

用户目标：{user_text}

相关技能：
{skill_context}

分析这些参考图片，然后提供结构化的 JSON 响应：
{{
  "reference_analysis": [
    {{
      "image_index": 0,
      "summary": "你看到的简要描述（中文）",
      "composition": "构图类型（例如：中景人像、广角镜头）",
      "lighting": "光照描述（中文）",
      "subject_position": "主体位置描述（中文）",
      "emotional_tone": "情感基调（中文）"
    }}
  ],
  "shot_plan": [
    {{"stage": "establish", "shot": "wide_context", "reason": "为什么需要这个镜头（中文）"}},
    {{"stage": "subject", "shot": "medium_portrait", "reason": "为什么需要这个镜头（中文）"}},
    {{"stage": "result", "shot": "reaction", "reason": "为什么需要这个镜头（中文）"}}
  ],
  "confidence": 0.85,
  "user_summary_zh": "中文总结给用户看"
}}

只返回 JSON，不要 markdown 代码块。所有文本内容必须用中文。"""

            try:
                result = self.provider.vision(prompt, images, expect_json=True)

                # Extract structured data
                reference_analysis = result.get("reference_analysis", [])
                shot_plan = result.get("shot_plan", [])
                confidence = result.get("confidence", 0.75)
                user_summary_zh = result.get("user_summary_zh", "已生成导演拍摄计划。")

                # Fallback shot plan if none provided
                if not shot_plan:
                    shot_plan = [
                        {"stage": "establish", "shot": "wide_context", "reason": "Set up environment and context"},
                        {"stage": "subject", "shot": "medium_portrait", "reason": "Focus on subject with clear framing"},
                        {"stage": "result", "shot": "reaction", "reason": "Capture emotional response or result"}
                    ]

            except Exception as e:
                import traceback
                print(f"Warning: Vision analysis failed: {e}")
                print(f"Full error traceback:")
                traceback.print_exc()
                shot_plan = [
                    {"stage": "establish", "shot": "wide_context", "reason": "Set up environment and context"},
                    {"stage": "subject", "shot": "medium_portrait", "reason": "Focus on subject with clear framing"},
                    {"stage": "result", "shot": "reaction", "reason": "Capture emotional response or result"}
                ]
                confidence = 0.6
                user_summary_zh = f"已生成基础拍摄方案（视觉分析失败：{str(e)}）"
        else:
            shot_plan = [
                {"stage": "establish", "shot": "wide_context", "reason": "Set up environment and context"},
                {"stage": "subject", "shot": "medium_portrait", "reason": "Focus on subject with clear framing"},
                {"stage": "result", "shot": "reaction", "reason": "Capture emotional response or result"}
            ]
            confidence = 0.7
            user_summary_zh = "已生成拍摄前导演方案：先建立环境，再突出人物，最后保留情绪结果。"

        return {
            "goal": user_text,
            "skills": [s["id"] for s in skills],
            "shot_plan": shot_plan,
            "reference_analysis": reference_analysis,
            "confidence": confidence,
            "user_summary_zh": user_summary_zh
        }
