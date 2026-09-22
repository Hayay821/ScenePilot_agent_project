"""
Director Plan Schema

Output from Director Agent.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class Priority(BaseModel):
    """Creative priority with weight"""
    name: str = Field(description="Priority name")
    weight: float = Field(ge=0.0, le=1.0, description="Weight 0.0-1.0")
    reason: Optional[str] = None


class ShotIntention(BaseModel):
    """Intended shot for a stage"""
    stage: str = Field(description="Stage name: prepare, peak, reaction, etc.")
    camera: str = Field(description="Preferred camera: x4air, link2")
    style: str = Field(description="Shot style: wide_context, full_body_tracking, etc.")
    duration_hint_sec: Optional[float] = None
    notes: Optional[str] = None


class Decision(BaseModel):
    """Director's decision on a rule or conflict"""
    rule_id: Optional[str] = None
    skill_id: Optional[str] = None
    selected: bool
    reason: str
    alternative: Optional[str] = None


class DirectorPlan(BaseModel):
    """
    Director Agent Output

    High-level creative plan for the shoot.
    Does NOT contain device commands.
    """
    plan_id: str
    intent_id: str
    session_id: str

    # Creative vision
    creative_goal: str = Field(description="Overall creative goal")
    priorities: List[Priority] = Field(description="Ordered priorities")

    # Shot planning
    shot_intentions: List[ShotIntention] = Field(description="Intended shots per stage")

    # Conflict resolution
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    decisions: List[Decision] = Field(default_factory=list)

    # Teaching
    teaching_notes: List[str] = Field(
        default_factory=list,
        description="Explanations for learners"
    )

    # Validation
    requires_human_approval: bool = False
    warnings: List[str] = Field(default_factory=list)

    # Metadata
    skill_bundle_id: str
    created_at: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    def get_shot_for_stage(self, stage: str) -> Optional[ShotIntention]:
        """Get shot intention for a specific stage"""
        for shot in self.shot_intentions:
            if shot.stage == stage:
                return shot
        return None

    def is_executable(self) -> bool:
        """Check if plan is ready for execution"""
        return (
            self.confidence >= 0.7 and
            len(self.shot_intentions) > 0 and
            not self.requires_human_approval
        )
