"""
Director Agent

Creates high-level creative plans for shoots.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from .base_agent import BaseAgent
from ..schemas import (
    AgentType,
    AgentResult,
    DirectorPlan,
    Priority,
    ShotIntention,
    Decision,
    SkillBundle,
)


class DirectorAgent(BaseAgent):
    """
    Director Agent

    Responsibilities:
    1. Create creative vision and priorities
    2. Plan shot intentions per stage
    3. Resolve conflicts between skills
    4. Output high-level plan (NO device commands)
    """

    def __init__(self, model_provider: Optional[Any] = None):
        super().__init__(AgentType.DIRECTOR, model_provider)

    def process(self, context: Dict[str, Any]) -> AgentResult:
        """
        Process intent and skills to create director plan

        Context keys:
        - intent: NormalizedIntent
        - skill_bundle: SkillBundle
        - session_id: Session identifier
        - events: Optional list of detected events
        """
        intent = context.get("intent")
        skill_bundle = context.get("skill_bundle")
        session_id = context.get("session_id", "session_unknown")
        events = context.get("events", [])

        if not intent or not skill_bundle:
            raise ValueError("Intent and skill_bundle are required")

        # Use model provider or mock
        if self.model_provider:
            from ..schemas import DirectorPlan as PlanSchema
            response = self.model_provider.generate(
                prompt=self._build_prompt(intent, skill_bundle, events),
                schema=PlanSchema,
            )
        else:
            # Fallback: rule-based plan
            response = self._create_rule_based_plan(intent, skill_bundle, session_id)

        # Create DirectorPlan
        plan = DirectorPlan(**response)

        # Create result
        result = self._create_result(
            session_id=session_id,
            intent_id=intent.get("intent_id") if isinstance(intent, dict) else intent.intent_id,
            output=plan,
            confidence=plan.confidence,
            skill_bundle_id=skill_bundle.bundle_id if hasattr(skill_bundle, "bundle_id") else "unknown",
        )

        # Add teaching notes
        if intent.get("teaching_mode") if isinstance(intent, dict) else intent.teaching_mode:
            result.teaching_notes = plan.teaching_notes

        return result

    def _build_prompt(self, intent: Any, skill_bundle: Any, events: list) -> str:
        """Build prompt for LLM"""
        prompt = f"""
作为导演AI，根据用户意图和摄影技能创建拍摄计划。

用户意图: {intent}
可用技能: {skill_bundle}
已检测事件: {events}

请输出:
1. 创意目标
2. 优先级排序
3. 各阶段的镜头意图
4. 冲突解决方案
5. 教学说明
"""
        return prompt

    def _create_rule_based_plan(
        self,
        intent: Any,
        skill_bundle: Any,
        session_id: str
    ) -> Dict[str, Any]:
        """Create plan using rules from skill bundle"""
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"

        # Extract intent data
        if isinstance(intent, dict):
            intent_id = intent.get("intent_id", "unknown")
            goal = intent.get("goal", {})
        else:
            intent_id = intent.intent_id
            goal = intent.goal.model_dump()

        # Extract skills
        if isinstance(skill_bundle, dict):
            skills = skill_bundle.get("skills", [])
            bundle_id = skill_bundle.get("bundle_id", "unknown")
        else:
            skills = skill_bundle.skills
            bundle_id = skill_bundle.bundle_id

        # Determine creative goal
        goal_type = goal.get("goal_type", "general")
        creative_goal_map = {
            "action_story": "突出动作完整弧线和情绪反应",
            "travel_story": "建立环境氛围，记录探索过程",
            "team_moment": "平衡团队关系和个体表情",
        }
        creative_goal = creative_goal_map.get(goal_type, "记录精彩瞬间")

        # Build priorities from skills
        priorities = []
        for skill in skills:
            if isinstance(skill, dict):
                skill_rules = skill.get("rules", [])
            else:
                skill_rules = skill.rules

            for rule in skill_rules:
                rule_data = rule if isinstance(rule, dict) else rule.model_dump()
                priorities.append({
                    "name": rule_data.get("id"),
                    "weight": rule_data.get("priority", 50) / 100.0,
                    "reason": rule_data.get("explanation", "")
                })

        # Sort by weight
        priorities.sort(key=lambda p: p["weight"], reverse=True)
        priorities = priorities[:5]  # Top 5

        # Create shot intentions based on common stages
        shot_intentions = [
            {
                "stage": "prepare",
                "camera": "x4air",
                "style": "wide_context",
                "duration_hint_sec": 3.0,
                "notes": "建立环境和准备状态"
            },
            {
                "stage": "main",
                "camera": "link2",
                "style": "full_body_tracking",
                "duration_hint_sec": 10.0,
                "notes": "主要内容拍摄"
            },
            {
                "stage": "reaction",
                "camera": "x4air",
                "style": "group_context",
                "duration_hint_sec": 4.0,
                "notes": "情绪反应和结尾"
            }
        ]

        # Create decisions
        decisions = []
        for priority in priorities[:3]:
            decisions.append({
                "rule_id": priority["name"],
                "skill_id": "unknown",
                "selected": True,
                "reason": "高优先级规则"
            })

        return {
            "plan_id": plan_id,
            "intent_id": intent_id,
            "session_id": session_id,
            "creative_goal": creative_goal,
            "priorities": priorities,
            "shot_intentions": shot_intentions,
            "conflicts": [],
            "decisions": decisions,
            "teaching_notes": [
                f"根据{goal_type}类型，采用{len(shot_intentions)}段式拍摄",
                "保留完整叙事弧线，避免只截取高潮片段",
            ],
            "requires_human_approval": False,
            "warnings": [],
            "skill_bundle_id": bundle_id,
            "created_at": datetime.utcnow().isoformat(),
            "confidence": 0.82,
        }
