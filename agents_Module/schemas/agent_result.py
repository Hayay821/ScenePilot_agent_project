"""
Agent Result Schema

Common wrapper for all agent outputs.
"""

from typing import Optional, Dict, Any, List, Union
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class AgentType(str, Enum):
    """Agent types"""
    SKILLS_MANAGER = "skills_manager"
    DIRECTOR = "director"
    CINEMATOGRAPHER = "cinematographer"
    EDITOR = "editor"


class EvidenceReference(BaseModel):
    """Reference to evidence supporting agent output"""
    type: str = Field(description="Evidence type: image, video, event, detection")
    id: str
    path: Optional[str] = None
    timestamp_ms: Optional[int] = None
    confidence: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentResult(BaseModel):
    """
    Common result wrapper for all agents

    Provides consistent structure for:
    - Output validation
    - Audit logging
    - Human approval workflow
    - Teaching mode
    """
    # Identity
    agent_name: AgentType
    schema_version: str = Field(default="1.0")
    result_id: str

    # Session context
    session_id: str
    intent_id: Optional[str] = None

    # Output (polymorphic based on agent type)
    output: Union[
        Dict[str, Any],  # Generic dict for flexibility
        BaseModel,       # Or specific schema
    ]

    # Evidence and reasoning
    evidence_refs: List[EvidenceReference] = Field(default_factory=list)
    explanation: Optional[str] = None
    reasoning_steps: List[str] = Field(default_factory=list)

    # Confidence and validation
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

    # Human review
    requires_human_approval: bool = False
    approval_reason: Optional[str] = None

    # Teaching mode
    teaching_notes: List[str] = Field(default_factory=list)
    user_level: str = Field(default="beginner")

    # Skills used
    skill_bundle_id: Optional[str] = None
    skills_used: List[str] = Field(default_factory=list)

    # Model metadata
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    prompt_version: Optional[str] = None

    # Timing
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    execution_time_ms: Optional[float] = None

    def is_successful(self) -> bool:
        """Check if result is successful"""
        return (
            len(self.errors) == 0 and
            self.confidence >= 0.6 and
            self.output is not None
        )

    def needs_approval(self) -> bool:
        """Check if human approval is needed"""
        return (
            self.requires_human_approval or
            len(self.warnings) > 0 or
            self.confidence < 0.75
        )

    def add_warning(self, message: str):
        """Add a warning message"""
        self.warnings.append(message)

    def add_error(self, message: str):
        """Add an error message"""
        self.errors.append(message)

    def add_evidence(self, evidence: EvidenceReference):
        """Add evidence reference"""
        self.evidence_refs.append(evidence)
