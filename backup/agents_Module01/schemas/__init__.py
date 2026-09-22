"""
Schemas for the Four Agent System

Core data structures:
- SkillManifest: Photography skill definition
- NormalizedIntent: User intent after processing by Skills Manager
- DirectorPlan: Output from Director Agent
- CinematographerRecommendation: Output from Cinematographer Agent
- EditPlan: Output from Editor Agent
- AgentResult: Common result wrapper
"""

from .skill import (
    SkillManifest,
    SkillRule,
    SkillBundle,
    SkillAuthor,
    SkillTeaching,
    SkillSafety,
    SkillEvidence,
    SkillStatus,
    SkillVisibility,
)

from .intent import (
    NormalizedIntent,
    UserGoal,
    OutputRequirement,
    SkillQuery,
)

from .plan import (
    DirectorPlan,
    ShotIntention,
    Priority,
    Decision,
)

from .recommendation import (
    CinematographerRecommendation,
    ShotStrategy,
    SuggestedAction,
    SubjectState,
)

from .edit_plan import (
    EditPlan,
    TimelineSegment,
    PanoramaTrack,
    RenderConfig,
)

from .agent_result import (
    AgentResult,
    AgentType,
    EvidenceReference,
)

from .event import (
    Event,
    EventType,
)

from .user_level import UserLevel

__all__ = [
    # Skill
    "SkillManifest",
    "SkillRule",
    "SkillBundle",
    "SkillAuthor",
    "SkillTeaching",
    "SkillSafety",
    "SkillEvidence",
    "SkillStatus",
    "SkillVisibility",

    # Intent
    "NormalizedIntent",
    "UserGoal",
    "OutputRequirement",
    "SkillQuery",

    # Plan
    "DirectorPlan",
    "ShotIntention",
    "Priority",
    "Decision",

    # Recommendation
    "CinematographerRecommendation",
    "ShotStrategy",
    "SuggestedAction",
    "SubjectState",

    # Edit Plan
    "EditPlan",
    "TimelineSegment",
    "PanoramaTrack",
    "RenderConfig",

    # Agent Result
    "AgentResult",
    "AgentType",
    "EvidenceReference",

    # Event
    "Event",
    "EventType",

    # User Level
    "UserLevel",
]
