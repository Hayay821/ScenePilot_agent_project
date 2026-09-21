"""
Cinematographer Agent

Provides real-time shot recommendations during filming.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from .base_agent import BaseAgent
from ..schemas import (
    AgentType,
    AgentResult,
    CinematographerRecommendation,
    ShotStrategy,
    SuggestedAction,
    SubjectState,
)


class CinematographerAgent(BaseAgent):
    """
    Cinematographer Agent

    Responsibilities:
    1. Analyze current subject state
    2. Determine shot strategy based on director plan
    3. Suggest device actions (NOT execute)
    4. Provide real-time recommendations
    """

    def __init__(self, model_provider: Optional[Any] = None):
        super().__init__(AgentType.CINEMATOGRAPHER, model_provider)

    def process(self, context: Dict[str, Any]) -> AgentResult:
        """
        Process current state and create recommendation

        Context keys:
        - plan: DirectorPlan
        - subject: Current subject state (optional)
        - timestamp_ms: Current timestamp
        - session_id: Session identifier
        - current_stage: Current stage name
        """
        plan = context.get("plan")
        subject = context.get("subject")
        timestamp_ms = context.get("timestamp_ms", 0)
        session_id = context.get("session_id", "session_unknown")
        current_stage = context.get("current_stage", "main")

        if not plan:
            raise ValueError("DirectorPlan is required")

        # Use model provider or mock
        if self.model_provider:
            from ..schemas import CinematographerRecommendation as RecSchema
            response = self.model_provider.generate(
                prompt=self._build_prompt(plan, subject, current_stage),
                schema=RecSchema,
            )
        else:
            # Fallback: rule-based recommendation
            response = self._create_rule_based_recommendation(
                plan, subject, timestamp_ms, session_id, current_stage
            )

        # Create recommendation
        recommendation = CinematographerRecommendation(**response)

        # Create result
        result = self._create_result(
            session_id=session_id,
            intent_id=plan.get("intent_id") if isinstance(plan, dict) else plan.intent_id,
            output=recommendation,
            confidence=recommendation.confidence,
        )

        return result

    def _build_prompt(self, plan: Any, subject: Any, stage: str) -> str:
        """Build prompt for LLM"""
        prompt = f"""
作为摄影指导AI，根据导演计划和当前主体状态提供拍摄建议。

导演计划: {plan}
当前主体: {subject}
当前阶段: {stage}

请输出:
1. 镜头策略（构图、相机选择、跟踪速度）
2. 建议的设备动作（仅建议，不执行）
3. 理由说明
"""
        return prompt

    def _create_rule_based_recommendation(
        self,
        plan: Any,
        subject: Optional[Any],
        timestamp_ms: int,
        session_id: str,
        current_stage: str
    ) -> Dict[str, Any]:
        """Create recommendation based on plan rules"""
        rec_id = f"rec_{uuid.uuid4().hex[:8]}"

        # Extract plan data
        if isinstance(plan, dict):
            plan_id = plan.get("plan_id", "unknown")
            shot_intentions = plan.get("shot_intentions", [])
        else:
            plan_id = plan.plan_id
            shot_intentions = [s.model_dump() for s in plan.shot_intentions]

        # Find matching shot intention for current stage
        shot_intention = None
        for intention in shot_intentions:
            if intention.get("stage") == current_stage:
                shot_intention = intention
                break

        # Default shot strategy
        if shot_intention:
            composition = "full_body" if "body" in shot_intention.get("style", "") else "wide"
            camera_preference = shot_intention.get("camera", "link2")
        else:
            composition = "full_body"
            camera_preference = "link2"

        # Subject state
        subject_data = None
        if subject:
            if isinstance(subject, dict):
                subject_data = subject
            else:
                subject_data = subject.model_dump()

        # Determine state
        if subject_data:
            state = "tracking"
        else:
            state = "idle"

        # Create suggested actions
        suggested_actions = []
        if subject_data and state == "tracking":
            suggested_actions.append({
                "device": camera_preference,
                "action": "suggest_composition",
                "args": {"style": composition},
                "reason": f"{current_stage}阶段需要{composition}构图",
                "confidence": 0.85,
                "priority": 90
            })

            if subject_data.get("motion_vector"):
                suggested_actions.append({
                    "device": camera_preference,
                    "action": "suggest_tracking",
                    "args": {"speed": "normal"},
                    "reason": "主体正在移动，建议跟踪",
                    "confidence": 0.80,
                    "priority": 85
                })

        return {
            "recommendation_id": rec_id,
            "plan_id": plan_id,
            "timestamp_ms": timestamp_ms,
            "state": state,
            "subject": subject_data,
            "shot_strategy": {
                "composition": composition,
                "camera_preference": camera_preference,
                "tracking_speed": "normal",
                "keep_pre_roll_ms": 3000,
                "keep_post_roll_ms": None,
                "frame_subject": True
            },
            "suggested_actions": suggested_actions,
            "current_stage": current_stage,
            "active_rules": [shot_intention.get("stage")] if shot_intention else [],
            "explanation": f"{current_stage}阶段，使用{composition}构图，{camera_preference}相机",
            "requires_executor_validation": True,
            "warnings": [],
            "created_at": datetime.utcnow().isoformat(),
            "confidence": 0.82,
        }
