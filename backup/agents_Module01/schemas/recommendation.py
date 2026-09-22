"""
Cinematographer Recommendation Schema

Output from Cinematographer Agent.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class SubjectState(BaseModel):
    """Current state of the subject being tracked"""
    id: str
    type: str = Field(description="Subject type: person, vehicle, object")
    bbox: List[float] = Field(description="Bounding box [x, y, w, h] normalized 0-1")
    confidence: float = Field(ge=0.0, le=1.0)
    motion_vector: Optional[List[float]] = None
    pose: Optional[str] = None


class ShotStrategy(BaseModel):
    """Strategy for current shot"""
    composition: str = Field(description="Composition: full_body, half_body, close_up, wide")
    camera_preference: str = Field(description="Preferred camera: link2, x4air")
    tracking_speed: Optional[str] = Field(default="normal", description="Tracking speed: slow, normal, fast")
    keep_pre_roll_ms: Optional[int] = None
    keep_post_roll_ms: Optional[int] = None
    frame_subject: bool = Field(default=True)


class SuggestedAction(BaseModel):
    """
    Suggested device action

    IMPORTANT: This is a SUGGESTION, not a command.
    Must be validated by DeviceExecutor before execution.
    """
    device: str = Field(description="Target device: link2, x4air")
    action: str = Field(description="Action type: set_composition, start_tracking, etc.")
    args: Dict[str, Any] = Field(description="Action arguments")
    reason: str = Field(description="Reason for this action")
    confidence: float = Field(ge=0.0, le=1.0)
    priority: int = Field(default=50, ge=0, le=100)


class CinematographerRecommendation(BaseModel):
    """
    Cinematographer Agent Output

    Real-time shot recommendations during filming.
    """
    recommendation_id: str
    plan_id: str
    timestamp_ms: int

    # Current state
    state: str = Field(description="Current state: idle, tracking, framing, transition")
    subject: Optional[SubjectState] = None

    # Shot strategy
    shot_strategy: ShotStrategy

    # Device suggestions (NOT commands)
    suggested_actions: List[SuggestedAction] = Field(default_factory=list)

    # Context from director plan
    current_stage: Optional[str] = None
    active_rules: List[str] = Field(default_factory=list)

    # Teaching
    explanation: Optional[str] = None

    # Safety
    requires_executor_validation: bool = Field(default=True)
    warnings: List[str] = Field(default_factory=list)

    # Metadata
    created_at: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    def get_primary_action(self) -> Optional[SuggestedAction]:
        """Get highest priority action"""
        if not self.suggested_actions:
            return None
        return max(self.suggested_actions, key=lambda a: a.priority)

    def is_safe_to_execute(self) -> bool:
        """Check if recommendation is safe to execute"""
        return (
            self.confidence >= 0.75 and
            len(self.warnings) == 0 and
            self.requires_executor_validation
        )
