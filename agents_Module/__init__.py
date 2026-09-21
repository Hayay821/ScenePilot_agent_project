"""
ScenePilot Agent Module

Multi-agent system for intelligent photography assistance.
"""

__version__ = "0.1.0"

from agents_Module.agents import (
    BaseAgent,
    SkillsManagerAgent,
    DirectorAgent,
    CinematographerAgent,
    EditorAgent,
)

from agents_Module.skills import (
    SkillRepository,
    SkillValidator,
)

from agents_Module.orchestration import AgentOrchestrator

from agents_Module.schemas import (
    AgentType,
    AgentResult,
    UserLevel,
    SkillManifest,
    NormalizedIntent,
    DirectorPlan,
    CinematographerRecommendation,
    EditPlan,
)

__all__ = [
    # Version
    "__version__",

    # Agents
    "BaseAgent",
    "SkillsManagerAgent",
    "DirectorAgent",
    "CinematographerAgent",
    "EditorAgent",

    # Skills
    "SkillRepository",
    "SkillValidator",

    # Orchestration
    "AgentOrchestrator",

    # Schemas
    "AgentType",
    "AgentResult",
    "UserLevel",
    "SkillManifest",
    "NormalizedIntent",
    "DirectorPlan",
    "CinematographerRecommendation",
    "EditPlan",
]
