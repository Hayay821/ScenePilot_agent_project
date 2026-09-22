"""
Agent Orchestrator

Coordinates the four agents through the filming workflow.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import json
import uuid

from ..agents import (
    SkillsManagerAgent,
    DirectorAgent,
    CinematographerAgent,
    EditorAgent,
)
from ..schemas import AgentResult, AgentType
from ..skills import SkillRepository, SkillValidator


class WorkflowStage:
    """Workflow stages"""
    PRE_PRODUCTION = "pre_production"
    FILMING = "filming"
    POST_PRODUCTION = "post_production"


class AgentOrchestrator:
    """
    Agent Orchestrator

    Coordinates the four agents through the complete workflow:
    1. Pre-production: Intent normalization -> Skill retrieval -> Director planning
    2. Filming: Real-time cinematographer recommendations
    3. Post-production: Editor timeline creation
    """

    def __init__(
        self,
        skill_repository: SkillRepository,
        skill_validator: SkillValidator,
        model_provider: Optional[Any] = None,
        audit_log_path: Optional[str] = None,
    ):
        """
        Initialize orchestrator

        Args:
            skill_repository: Skill repository
            skill_validator: Skill validator
            model_provider: Model provider for agents
            audit_log_path: Path to save audit logs
        """
        # Initialize agents
        self.skills_manager = SkillsManagerAgent(
            skill_repository=skill_repository,
            skill_validator=skill_validator,
            model_provider=model_provider,
        )
        self.director = DirectorAgent(model_provider=model_provider)
        self.cinematographer = CinematographerAgent(model_provider=model_provider)
        self.editor = EditorAgent(model_provider=model_provider)

        self.repository = skill_repository
        self.validator = skill_validator
        self.audit_log_path = Path(audit_log_path) if audit_log_path else None

        # Session state
        self.session_id = f"session_{uuid.uuid4().hex[:8]}"
        self.current_stage = WorkflowStage.PRE_PRODUCTION
        self.context = {}
        self.results = []

    def run_pre_production(
        self,
        user_input: str,
        available_devices: List[str] = None,
        user_level: str = "beginner",
    ) -> Dict[str, AgentResult]:
        """
        Run pre-production workflow

        Steps:
        1. Normalize user intent
        2. Retrieve relevant skills
        3. Create skill bundle
        4. Generate director plan

        Args:
            user_input: User's description of what they want to film
            available_devices: List of available devices
            user_level: User skill level

        Returns:
            Dictionary of agent results
        """
        if available_devices is None:
            available_devices = ["link2", "x4air"]

        results = {}

        # Step 1: Normalize intent
        intent_result = self.skills_manager.process({
            "task": "normalize_intent",
            "user_input": user_input,
            "session_id": self.session_id,
            "available_devices": available_devices,
            "user_level": user_level,
        })
        results["intent"] = intent_result
        self._save_result(intent_result)

        if not intent_result.is_successful():
            return results

        intent = intent_result.output

        # Step 2: Retrieve skills
        skill_result = self.skills_manager.process({
            "task": "retrieve_skills",
            "intent": intent,
            "session_id": self.session_id,
        })
        results["skills"] = skill_result
        self._save_result(skill_result)

        if not skill_result.is_successful() or not skill_result.output.get("skills"):
            return results

        # Step 3: Create skill bundle
        bundle_result = self.skills_manager.process({
            "task": "create_bundle",
            "skills": skill_result.output["skills"],
            "intent_id": intent["intent_id"],
            "session_id": self.session_id,
        })
        results["bundle"] = bundle_result
        self._save_result(bundle_result)

        if not bundle_result.is_successful():
            return results

        skill_bundle = bundle_result.output

        # Step 4: Generate director plan
        plan_result = self.director.process({
            "intent": intent,
            "skill_bundle": skill_bundle,
            "session_id": self.session_id,
        })
        results["plan"] = plan_result
        self._save_result(plan_result)

        # Save to context for later stages
        self.context["intent"] = intent
        self.context["skill_bundle"] = skill_bundle
        self.context["plan"] = plan_result.output

        return results

    def run_filming_step(
        self,
        subject: Optional[Dict[str, Any]] = None,
        timestamp_ms: int = 0,
        current_stage: str = "main",
    ) -> AgentResult:
        """
        Run single filming step

        Args:
            subject: Current subject state
            timestamp_ms: Current timestamp
            current_stage: Current stage name

        Returns:
            Cinematographer recommendation result
        """
        if "plan" not in self.context:
            raise RuntimeError("Must run pre_production before filming")

        recommendation_result = self.cinematographer.process({
            "plan": self.context["plan"],
            "subject": subject,
            "timestamp_ms": timestamp_ms,
            "session_id": self.session_id,
            "current_stage": current_stage,
        })

        self._save_result(recommendation_result)
        return recommendation_result

    def run_post_production(
        self,
        events: List[Any] = None,
        media_sources: List[Dict[str, Any]] = None,
    ) -> AgentResult:
        """
        Run post-production workflow

        Args:
            events: List of detected events
            media_sources: Available media sources

        Returns:
            Editor edit plan result
        """
        if "plan" not in self.context or "intent" not in self.context:
            raise RuntimeError("Must run pre_production before post_production")

        if events is None:
            events = []
        if media_sources is None:
            media_sources = []

        edit_result = self.editor.process({
            "plan": self.context["plan"],
            "events": events,
            "media_sources": media_sources,
            "intent": self.context["intent"],
            "session_id": self.session_id,
        })

        self._save_result(edit_result)
        return edit_result

    def run_complete_workflow(
        self,
        user_input: str,
        available_devices: List[str] = None,
        user_level: str = "beginner",
        events: List[Any] = None,
        media_sources: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run complete workflow from intent to edit plan

        Args:
            user_input: User's description
            available_devices: Available devices
            user_level: User skill level
            events: Detected events (for post-production)
            media_sources: Media sources (for post-production)

        Returns:
            Dictionary with all results
        """
        # Pre-production
        pre_results = self.run_pre_production(
            user_input=user_input,
            available_devices=available_devices,
            user_level=user_level,
        )

        # Post-production
        if "plan" in pre_results and pre_results["plan"].is_successful():
            edit_result = self.run_post_production(
                events=events,
                media_sources=media_sources,
            )
            pre_results["edit"] = edit_result

        return pre_results

    def _save_result(self, result: AgentResult):
        """Save result to audit log"""
        self.results.append(result)

        if self.audit_log_path:
            self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)

            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "session_id": self.session_id,
                "agent": result.agent_name.value,
                "result_id": result.result_id,
                "confidence": result.confidence,
                "warnings": result.warnings,
                "errors": result.errors,
                "output": result.output,
            }

            with open(self.audit_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        return {
            "session_id": self.session_id,
            "stage": self.current_stage,
            "results_count": len(self.results),
            "has_intent": "intent" in self.context,
            "has_plan": "plan" in self.context,
            "has_bundle": "skill_bundle" in self.context,
        }

    def reset_session(self):
        """Reset session for new workflow"""
        self.session_id = f"session_{uuid.uuid4().hex[:8]}"
        self.current_stage = WorkflowStage.PRE_PRODUCTION
        self.context = {}
        self.results = []
