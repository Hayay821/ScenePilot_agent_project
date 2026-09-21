"""
Skills Manager Agent

Handles user intent normalization, skill retrieval, and expert knowledge ingestion.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from .base_agent import BaseAgent
from ..schemas import (
    AgentType,
    AgentResult,
    NormalizedIntent,
    SkillBundle,
    SkillManifest,
)
from ..skills import SkillRepository, SkillValidator


class SkillsManagerAgent(BaseAgent):
    """
    Skills Manager Agent

    Responsibilities:
    1. Normalize user intent from natural language
    2. Retrieve and rank relevant skills
    3. Create skill bundles for other agents
    4. Ingest expert knowledge from images/text
    5. Manage skill lifecycle (draft -> review -> published)
    """

    def __init__(
        self,
        skill_repository: SkillRepository,
        skill_validator: SkillValidator,
        model_provider: Optional[Any] = None,
    ):
        super().__init__(AgentType.SKILLS_MANAGER, model_provider)
        self.repository = skill_repository
        self.validator = skill_validator

    def process(self, context: Dict[str, Any]) -> AgentResult:
        """
        Process user input

        Context keys:
        - task: "normalize_intent" | "retrieve_skills" | "create_bundle"
        - user_input: Raw user description
        - session_id: Session identifier
        - available_devices: List of available devices
        - user_level: User skill level
        """
        task = context.get("task", "normalize_intent")

        if task == "normalize_intent":
            return self._normalize_intent(context)
        elif task == "retrieve_skills":
            return self._retrieve_skills(context)
        elif task == "create_bundle":
            return self._create_bundle(context)
        else:
            raise ValueError(f"Unknown task: {task}")

    def _normalize_intent(self, context: Dict[str, Any]) -> AgentResult:
        """
        Normalize user intent from natural language

        Returns NormalizedIntent as output.
        """
        user_input = context.get("user_input", "")
        session_id = context.get("session_id", f"session_{uuid.uuid4().hex[:8]}")
        available_devices = context.get("available_devices", ["link2", "x4air"])
        user_level = context.get("user_level", "beginner")

        # Use model provider or mock
        if self.model_provider:
            from ..schemas import NormalizedIntent as IntentSchema
            response = self.model_provider.generate(
                prompt=f"Normalize user intent: {user_input}",
                schema=IntentSchema,
            )
        else:
            # Fallback: simple keyword-based normalization
            response = self._simple_normalize(user_input, session_id, available_devices)

        # Create NormalizedIntent
        intent = NormalizedIntent(**response)

        # Create result
        result = self._create_result(
            session_id=session_id,
            intent_id=intent.intent_id,
            output=intent,
            confidence=intent.confidence,
        )

        # Add teaching notes
        if user_level == "beginner":
            result.teaching_notes = [
                f"您想拍摄的是: {intent.goal.goal_type}",
                f"建议使用的设备: {', '.join(available_devices)}",
                f"推荐的拍摄风格: {intent.goal.style or '标准'}",
            ]

        return result

    def _simple_normalize(
        self,
        user_input: str,
        session_id: str,
        available_devices: List[str]
    ) -> Dict[str, Any]:
        """Simple keyword-based normalization"""
        intent_id = f"intent_{uuid.uuid4().hex[:8]}"

        # Detect goal type from keywords
        goal_type = "general"
        if any(kw in user_input for kw in ["动作", "运动", "挑战"]):
            goal_type = "action_story"
        elif any(kw in user_input for kw in ["旅行", "探索", "风景"]):
            goal_type = "travel_story"
        elif any(kw in user_input for kw in ["团队", "聚会", "多人"]):
            goal_type = "team_moment"

        # Detect style
        style = None
        if "热血" in user_input:
            style = "热血"
        elif "轻松" in user_input:
            style = "轻松"
        elif "教学" in user_input:
            style = "教学"

        return {
            "intent_id": intent_id,
            "session_id": session_id,
            "raw_input": user_input,
            "goal": {
                "goal_type": goal_type,
                "subject": "single_person",
                "priority": ["clarity", "peak_moment"],
                "style": style,
            },
            "output": {
                "duration_sec": 30,
                "ratio": "9:16",
                "format": "mp4",
                "quality": "high",
            },
            "skill_query": {
                "tags": [],
                "agents": ["director", "cinematographer", "editor"],
                "devices": available_devices,
                "max_results": 3,
            },
            "user_level": "beginner",
            "teaching_mode": True,
            "available_devices": available_devices,
            "device_preferences": {},
            "constraints": {},
            "created_at": datetime.utcnow().isoformat(),
            "confidence": 0.75,
        }

    def _retrieve_skills(self, context: Dict[str, Any]) -> AgentResult:
        """
        Retrieve relevant skills based on intent

        Returns list of SkillManifest as output.
        """
        intent = context.get("intent")
        if not intent:
            raise ValueError("Intent is required for skill retrieval")

        session_id = context.get("session_id", "session_unknown")

        # Extract query from intent
        if isinstance(intent, dict):
            query = intent.get("skill_query", {})
        else:
            query = intent.skill_query.model_dump()

        # Search repository
        skills = self.repository.search(
            tags=query.get("tags", []),
            agent=query.get("agents", [None])[0] if query.get("agents") else None,
            max_results=query.get("max_results", 3),
        )

        # Validate skills
        valid_skills = []
        for skill in skills:
            is_valid, errors = self.validator.validate(skill)
            if is_valid:
                valid_skills.append(skill)

        # Create result
        result = self._create_result(
            session_id=session_id,
            intent_id=intent.get("intent_id") if isinstance(intent, dict) else intent.intent_id,
            output={"skills": [s.model_dump() for s in valid_skills]},
            confidence=0.9 if valid_skills else 0.3,
        )

        if not valid_skills:
            result.add_warning("No valid skills found for this intent")

        return result

    def _create_bundle(self, context: Dict[str, Any]) -> AgentResult:
        """
        Create skill bundle for use by other agents

        Returns SkillBundle as output.
        """
        skills = context.get("skills", [])
        intent_id = context.get("intent_id", "intent_unknown")
        session_id = context.get("session_id", "session_unknown")

        # Convert to SkillManifest if needed
        skill_objects = []
        for skill in skills:
            if isinstance(skill, dict):
                skill_objects.append(SkillManifest(**skill))
            else:
                skill_objects.append(skill)

        # Check for conflicts
        conflicts = []
        for i, skill1 in enumerate(skill_objects):
            for skill2 in skill_objects[i + 1:]:
                has_conflict, conflict_desc = self.validator.check_conflict(skill1, skill2)
                if has_conflict:
                    conflicts.extend(conflict_desc)

        # Create bundle
        bundle = SkillBundle(
            bundle_id=f"bundle_{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            skills=skill_objects,
            intent_id=intent_id,
            selected_at=datetime.utcnow().isoformat(),
            conflicts=conflicts,
            resolution_notes=[],
        )

        # Create result
        result = self._create_result(
            session_id=session_id,
            intent_id=intent_id,
            output=bundle,
            confidence=0.9 if not conflicts else 0.7,
            skill_bundle_id=bundle.bundle_id,
        )

        if conflicts:
            result.add_warning(f"Found {len(conflicts)} skill conflicts")

        return result
