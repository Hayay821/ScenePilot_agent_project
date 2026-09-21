"""
Skill Manifest Schema

Photography skill definition following the Open Vision design.
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class SkillStatus(str, Enum):
    """Skill lifecycle status"""
    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"


class SkillVisibility(str, Enum):
    """Skill visibility scope"""
    LOCAL = "local"
    PRIVATE = "private"
    PUBLIC = "public"


class AuthorType(str, Enum):
    """Author type"""
    USER = "user"
    EXPERT = "expert"
    AI_GENERATED = "ai_generated"
    COMMUNITY = "community"


class SkillAuthor(BaseModel):
    """Skill author information"""
    type: AuthorType
    id: str
    display_name: str
    verified: bool = False


class SkillTeaching(BaseModel):
    """Teaching layer for human understanding"""
    audience: str = Field(description="Target audience: beginner, intermediate, expert")
    principles: List[str] = Field(description="Photography principles taught")
    explain_template: str = Field(description="Template for explaining to users")

    @field_validator("audience")
    @classmethod
    def validate_audience(cls, v):
        valid = ["beginner", "intermediate", "expert", "all"]
        if v not in valid:
            raise ValueError(f"audience must be one of {valid}")
        return v


class SkillSafety(BaseModel):
    """Safety constraints and permissions"""
    allowed_actions: List[str] = Field(description="Whitelist of allowed actions")
    requires_human_approval: List[str] = Field(
        default_factory=list,
        description="Actions requiring human approval"
    )
    forbidden_actions: List[str] = Field(
        default_factory=list,
        description="Explicitly forbidden actions"
    )
    min_confidence_for_device_suggestion: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Minimum confidence to suggest device actions"
    )


class SkillEvidence(BaseModel):
    """Evidence and examples"""
    examples: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Example media with annotations"
    )
    expert_notes: List[str] = Field(
        default_factory=list,
        description="Expert annotations and notes"
    )


class SkillRuleCondition(BaseModel):
    """Condition for when a rule applies"""
    event: Optional[str] = None
    confidence_gte: Optional[float] = None
    subject_type: Optional[str] = None
    device_available: Optional[str] = None
    custom: Optional[Dict[str, Any]] = None


class SkillRuleAdvice(BaseModel):
    """Advice/action suggested by a rule"""
    composition: Optional[str] = None
    camera_preference: Optional[str] = None
    tracking_speed: Optional[str] = None
    keep_pre_roll_ms: Optional[int] = None
    keep_post_roll_ms: Optional[int] = None
    mark_highlight: Optional[bool] = None
    panorama_reframe: Optional[str] = None
    custom: Optional[Dict[str, Any]] = None


class SkillRule(BaseModel):
    """Individual rule within a skill"""
    id: str = Field(description="Unique rule ID within skill")
    when: SkillRuleCondition = Field(description="Condition for activation")
    advice: SkillRuleAdvice = Field(description="Suggested action")
    priority: int = Field(ge=0, le=100, description="Priority 0-100")
    explanation: str = Field(description="Human-readable explanation")

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        if not 0 <= v <= 100:
            raise ValueError("priority must be between 0 and 100")
        return v


class SkillInputs(BaseModel):
    """Input requirements for a skill"""
    intent: Dict[str, Any] = Field(description="Expected intent structure")
    media_types: List[str] = Field(description="Supported media types")
    required_capabilities: List[str] = Field(
        default_factory=list,
        description="Required device/system capabilities"
    )


class SkillAgentBindings(BaseModel):
    """Which agents can use this skill"""
    director: bool = False
    cinematographer: bool = False
    editor: bool = False
    skills_manager: bool = True  # Always available to skills manager


class SkillManifest(BaseModel):
    """
    Complete Skill Manifest

    Represents a photography skill with:
    - Identity (name, version, author)
    - Teaching layer (principles, explanations)
    - Rules (conditions and advice)
    - Safety constraints
    - Evidence and examples
    """

    # Identity layer
    schema_version: str = Field(default="1.0")
    skill_id: str = Field(description="Unique skill identifier")
    version: str = Field(description="Semantic version")
    name: str = Field(description="Human-readable name")
    name_en: Optional[str] = None
    description: str = Field(description="Skill description")

    # Author and licensing
    author: SkillAuthor
    license: str = Field(default="CC-BY-4.0")
    visibility: SkillVisibility = Field(default=SkillVisibility.LOCAL)
    status: SkillStatus = Field(default=SkillStatus.DRAFT)
    parent_skill: Optional[str] = None

    # Teaching layer
    teaching: SkillTeaching

    # Input layer
    inputs: SkillInputs

    # Agent bindings
    agent_bindings: SkillAgentBindings

    # Rules layer
    rules: List[SkillRule]

    # Safety layer
    safety: SkillSafety

    # Evidence layer
    evidence: SkillEvidence = Field(default_factory=SkillEvidence)

    # Metadata
    tags: List[str] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    content_hash: Optional[str] = None

    @field_validator("rules")
    @classmethod
    def validate_rules(cls, v):
        if not v:
            raise ValueError("Skill must have at least one rule")

        # Check for duplicate rule IDs
        rule_ids = [rule.id for rule in v]
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError("Duplicate rule IDs found")

        return v

    @field_validator("safety")
    @classmethod
    def validate_safety(cls, v):
        # Ensure no overlap between allowed and forbidden
        allowed = set(v.allowed_actions)
        forbidden = set(v.forbidden_actions)

        overlap = allowed & forbidden
        if overlap:
            raise ValueError(f"Actions cannot be both allowed and forbidden: {overlap}")

        return v

    def can_publish(self) -> bool:
        """Check if skill can be published"""
        return (
            self.status == SkillStatus.REVIEW and
            self.visibility != SkillVisibility.LOCAL and
            len(self.rules) > 0
        )

    def is_compatible_with_agent(self, agent_type: str) -> bool:
        """Check if skill is compatible with given agent"""
        bindings = self.agent_bindings

        return {
            "director": bindings.director,
            "cinematographer": bindings.cinematographer,
            "editor": bindings.editor,
            "skills_manager": bindings.skills_manager,
        }.get(agent_type, False)


class SkillBundle(BaseModel):
    """
    Bundle of skills selected for a session

    Prepared by Skills Manager Agent for use by other agents.
    """
    bundle_id: str
    session_id: str
    skills: List[SkillManifest]
    intent_id: str
    selected_at: str

    # Conflict resolution
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    resolution_notes: List[str] = Field(default_factory=list)

    def get_skills_for_agent(self, agent_type: str) -> List[SkillManifest]:
        """Get skills compatible with specific agent"""
        return [
            skill for skill in self.skills
            if skill.is_compatible_with_agent(agent_type)
        ]

    def get_all_rules(self) -> List[tuple[str, SkillRule]]:
        """Get all rules from all skills with skill_id"""
        rules = []
        for skill in self.skills:
            for rule in skill.rules:
                rules.append((skill.skill_id, rule))
        return rules
