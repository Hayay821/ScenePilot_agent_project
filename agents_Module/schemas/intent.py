"""
Normalized Intent Schema

User intent after processing by Skills Manager Agent.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class UserGoal(BaseModel):
    """User's creative goal"""
    goal_type: str = Field(description="Type of goal: action_story, travel_vlog, team_moment, etc.")
    subject: str = Field(description="Main subject: single_person, group, object, etc.")
    priority: List[str] = Field(description="Ordered list of priorities")
    style: Optional[str] = None
    tone: Optional[str] = None


class OutputRequirement(BaseModel):
    """Output format requirements"""
    duration_sec: Optional[int] = None
    ratio: str = Field(default="16:9", description="Aspect ratio: 16:9, 9:16, 1:1")
    format: str = Field(default="mp4")
    quality: str = Field(default="high")


class SkillQuery(BaseModel):
    """Query parameters for skill retrieval"""
    tags: List[str] = Field(default_factory=list)
    agents: List[str] = Field(default_factory=list)
    devices: List[str] = Field(default_factory=list)
    max_results: int = Field(default=3, ge=1, le=10)


class NormalizedIntent(BaseModel):
    """
    Normalized user intent

    Output from Skills Manager Agent after processing raw user input.
    """
    intent_id: str
    session_id: str

    # Raw user input
    raw_input: str = Field(description="Original user description")

    # Structured goal
    goal: UserGoal

    # Output requirements
    output: OutputRequirement

    # Skill selection query
    skill_query: SkillQuery

    # Context
    user_level: str = Field(default="beginner", description="User skill level")
    teaching_mode: bool = Field(default=True, description="Enable teaching explanations")

    # Device context
    available_devices: List[str] = Field(default_factory=list)
    device_preferences: Dict[str, Any] = Field(default_factory=dict)

    # Constraints
    constraints: Dict[str, Any] = Field(default_factory=dict)

    # Metadata
    created_at: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    def is_valid(self) -> bool:
        """Check if intent is valid for processing"""
        return (
            self.confidence >= 0.6 and
            len(self.goal.priority) > 0 and
            len(self.available_devices) > 0
        )
