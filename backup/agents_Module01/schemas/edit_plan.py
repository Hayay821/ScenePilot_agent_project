"""
Edit Plan Schema

Output from Editor Agent.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class TimelineSegment(BaseModel):
    """Single segment in the edit timeline"""
    source_id: str = Field(description="Source media ID: x4air_001, link2_001")
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    role: str = Field(description="Narrative role: prepare, peak, reaction, transition")
    reason: str = Field(description="Why this segment was selected")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    # Optional enhancements
    speed: float = Field(default=1.0, gt=0.0, description="Playback speed")
    volume: float = Field(default=1.0, ge=0.0, le=1.0, description="Audio volume")
    effects: List[str] = Field(default_factory=list)


class PanoramaTrack(BaseModel):
    """
    Panorama reframe track point

    For equirectangular video reframing.
    """
    time_ms: int = Field(ge=0)
    yaw: float = Field(description="Yaw angle in degrees")
    pitch: float = Field(description="Pitch angle in degrees")
    fov: float = Field(default=90.0, ge=30.0, le=120.0, description="Field of view")

    # Optional easing
    easing: Optional[str] = Field(default="linear")


class SubtitleEntry(BaseModel):
    """Subtitle entry"""
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    text: str
    style: Optional[str] = None


class RenderConfig(BaseModel):
    """Render configuration"""
    ratio: str = Field(default="16:9")
    resolution: str = Field(default="1920x1080")
    fps: int = Field(default=30, ge=24, le=60)
    codec: str = Field(default="h264")
    quality: str = Field(default="high")


class EditPlan(BaseModel):
    """
    Editor Agent Output

    Post-production timeline and reframe plan.
    """
    edit_plan_id: str
    session_id: str
    intent_id: str

    # Timeline
    timeline: List[TimelineSegment] = Field(description="Edit timeline segments")

    # Panorama tracks (for X4 Air reframing)
    panorama_tracks: List[PanoramaTrack] = Field(
        default_factory=list,
        description="Panorama reframe tracks"
    )

    # Subtitles
    subtitles: List[SubtitleEntry] = Field(default_factory=list)

    # Render config
    render: RenderConfig

    # Metadata
    total_duration_ms: int = Field(ge=0)
    source_count: int = Field(ge=0)

    # Teaching
    explanations: List[str] = Field(
        default_factory=list,
        description="Explanations for edit decisions"
    )

    # Validation
    warnings: List[str] = Field(default_factory=list)

    # References
    plan_id: Optional[str] = None
    skill_bundle_id: Optional[str] = None

    # Metadata
    created_at: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    def validate_timeline(self) -> bool:
        """Validate timeline consistency"""
        if not self.timeline:
            return False

        # Check for time overlaps
        for i in range(len(self.timeline) - 1):
            if self.timeline[i].end_ms > self.timeline[i + 1].start_ms:
                return False

        return True

    def get_total_duration(self) -> int:
        """Calculate actual total duration from timeline"""
        if not self.timeline:
            return 0
        return self.timeline[-1].end_ms - self.timeline[0].start_ms
