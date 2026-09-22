"""Pydantic schemas for API request/response validation."""
from __future__ import annotations

from enum import Enum
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, model_validator


# ==================== Enums ====================

class MediaSourceType(str, Enum):
    """媒体源类型枚举"""
    FILE = "FILE"
    WEBCAM = "WEBCAM"


class ErrorCode(str, Enum):
    """错误代码枚举"""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    MEDIA_ERROR = "MEDIA_ERROR"
    CAMERA_ERROR = "CAMERA_ERROR"
    SKILL_NOT_FOUND = "SKILL_NOT_FOUND"
    API_ERROR = "API_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# ==================== Base Models ====================

class WebcamConfig(BaseModel):
    """摄像头配置"""
    camera_id: int = Field(default=0, description="摄像头 ID")
    frame_interval: float = Field(default=1.0, description="帧间隔（秒）")
    max_duration: Optional[float] = Field(default=None, description="最大捕获时长（秒）")
    resolution: Optional[List[int]] = Field(default=None, description="分辨率 [width, height]")


class MediaInput(BaseModel):
    """媒体输入"""
    source_type: MediaSourceType = Field(..., description="媒体源类型")
    paths: Optional[List[str]] = Field(default=None, description="文件路径列表（FILE 类型必填）")
    camera_config: Optional[WebcamConfig] = Field(default=None, description="摄像头配置（WEBCAM 类型必填）")

    @model_validator(mode="after")
    def validate_source(self):
        if self.source_type == MediaSourceType.FILE and not self.paths:
            raise ValueError("FILE media_input requires paths")
        if self.source_type == MediaSourceType.WEBCAM and not self.camera_config:
            raise ValueError("WEBCAM media_input requires camera_config")
        return self


class SkillsFilter(BaseModel):
    """技能筛选条件"""
    stage: Optional[str] = Field(default=None, description="阶段：director/cinematographer/editor")
    tags: Optional[List[str]] = Field(default=None, description="标签列表")
    limit: Optional[int] = Field(default=3, ge=1, le=20, description="返回数量限制")


class OutputConfig(BaseModel):
    """输出配置"""
    output_dir: Optional[str] = Field(default=None, description="输出目录")
    save_intermediate: Optional[bool] = Field(default=False, description="是否保存中间结果")
    formats: Optional[List[str]] = Field(default=None, description="输出格式列表")


class APIEnvelope(BaseModel):
    success: bool = True
    data: Any
    agent_type: Optional[str] = None
    timestamp: str


class APIError(BaseModel):
    code: ErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None


class APIErrorEnvelope(BaseModel):
    success: Literal[False] = False
    error: APIError
    timestamp: str


# ==================== Media API Models ====================

class MediaInfoResponse(BaseModel):
    """媒体信息响应"""
    path: str
    type: str  # "image", "video", "directory"
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    frames: Optional[int] = None
    duration: Optional[float] = None
    images: Optional[List[str]] = None
    videos: Optional[List[str]] = None


class MediaListResponse(BaseModel):
    """媒体列表响应"""
    images: List[str]
    videos: List[str]
    total: int


class ExtractFramesRequest(BaseModel):
    """提取视频帧请求"""
    video_path: str = Field(..., description="视频文件路径")
    output_dir: str = Field(..., description="输出目录")
    every_seconds: float = Field(default=2.0, description="每隔多少秒提取一帧")
    max_frames: int = Field(default=12, description="最大帧数")


class ExtractFramesResponse(BaseModel):
    """提取视频帧响应"""
    frames: List[str]
    total: int


class CaptureWebcamRequest(BaseModel):
    """摄像头捕获请求"""
    camera_id: int = Field(default=0, description="摄像头 ID")
    num_frames: int = Field(default=5, description="捕获帧数")
    interval: float = Field(default=1.0, description="捕获间隔（秒）")
    output_dir: str = Field(..., description="输出目录")
    resolution: Optional[List[int]] = Field(default=None, description="分辨率 [width, height]")


class CaptureWebcamResponse(BaseModel):
    """摄像头捕获响应"""
    frames: List[str]
    camera_id: int
    total: int


# ==================== Agent API Models ====================

class DirectorRequest(BaseModel):
    """Director Agent 请求"""
    user_text: str = Field(..., description="用户意图描述")
    media_input: MediaInput = Field(..., description="媒体输入")
    skills_filter: Optional[SkillsFilter] = Field(default=None, description="技能筛选条件")
    output_config: Optional[OutputConfig] = Field(default=None, description="输出配置")


class ShotPlanItem(BaseModel):
    """拍摄计划项"""
    stage: str
    shot: str
    reason: str


class ReferenceAnalysisItem(BaseModel):
    """参考图分析项"""
    image_index: int
    summary: str
    composition: str
    lighting: str
    subject_position: str
    emotional_tone: str


class DirectorResponse(BaseModel):
    """Director Agent 响应"""
    goal: str
    matched_skills: List[str]
    skills_guidance: str
    shot_plan: List[ShotPlanItem]
    reference_analysis: List[ReferenceAnalysisItem]
    confidence: float
    user_summary_zh: str


class CinematographerRequest(BaseModel):
    """Cinematographer Agent 请求"""
    user_text: str = Field(..., description="用户意图描述")
    media_input: MediaInput = Field(..., description="媒体输入")
    skills_filter: Optional[SkillsFilter] = Field(default=None, description="技能筛选条件")


class SourceFrame(BaseModel):
    """源帧信息"""
    path: str
    index: int
    timestamp_ms: int


class FrameAnalysis(BaseModel):
    """画面分析"""
    subject_visible: bool
    face_visible: bool
    tracking_confidence: float
    composition_quality: float
    summary: str
    confidence: float


class ShootingSuggestion(BaseModel):
    """拍摄建议"""
    action: str  # "capture_frame" or "wait_and_recheck"
    composition: str
    reason: str


class CinematographerResponse(BaseModel):
    """Cinematographer Agent 响应"""
    source_frames: List[SourceFrame]
    analysis: FrameAnalysis
    suggestion: ShootingSuggestion
    captured_frame: Optional[str]
    matched_skills: List[str]
    skills_guidance: str
    user_summary_zh: str


class CinematographerSessionStartRequest(BaseModel):
    user_text: str
    skills_filter: Optional[SkillsFilter] = None


class CinematographerFrameRequest(BaseModel):
    frame_data: str = Field(..., description="base64 image or data URL")


class CinematographerSessionStopRequest(BaseModel):
    session_id: str


class EditorRequest(BaseModel):
    """Editor Agent 请求"""
    user_text: str = Field(..., description="用户意图描述")
    media_input: MediaInput = Field(..., description="媒体输入")
    skills_filter: Optional[SkillsFilter] = Field(default=None, description="技能筛选条件")
    output_config: Optional[OutputConfig] = Field(default=None, description="输出配置")


class EditorWorkspaceRequest(BaseModel):
    """One-shot workspace transition demo."""
    v1_path: str
    v2_path: str
    reference_frame: Optional[str] = None
    prompt: str = "Smooth natural camera movement between the two shots. Preserve subject identity, motion direction, lighting continuity, and use the active editing skill rules."
    use_ai_transition: bool = True
    workspace_dir: Optional[str] = None


class EditorWorkspaceResponse(BaseModel):
    workspace_id: str
    workspace: str
    inputs: Dict[str, Any]
    frames: Dict[str, str]
    transition: Dict[str, Any]
    output_video: str
    pieces: List[str]
    prompt: str


class TimelineItem(BaseModel):
    """时间线项"""
    source: str
    role: str
    reason: str
    keep: bool
    ai_role: Optional[str] = None
    ai_reason: Optional[str] = None


class RenderConfig(BaseModel):
    """渲染配置"""
    ratio: str  # "9:16" or "16:9"
    format: str  # "mp4"


class EditorResponse(BaseModel):
    """Editor Agent 响应"""
    timeline: List[TimelineItem]
    rendered_preview: Optional[str]
    render: RenderConfig
    matched_skills: List[str]
    skills_guidance: str
    analysis_summary: str
    user_summary_zh: str


class RunAllRequest(BaseModel):
    """完整流程请求"""
    user_text: str = Field(..., description="用户意图描述")
    media_input: Optional[MediaInput] = Field(default=None, description="媒体输入")
    media_dir: Optional[str] = Field(default=None, description="媒体目录")
    output_config: Optional[OutputConfig] = Field(default=None, description="输出配置")


class RunAllResponse(BaseModel):
    """完整流程响应"""
    skills: List[Dict[str, Any]]
    director: DirectorResponse
    filming: CinematographerResponse
    editing: EditorResponse


# ==================== Skills API Models ====================

class SkillListItem(BaseModel):
    """技能列表项"""
    id: str
    name: str
    description: str
    stage: str
    tags: List[str]
    path: str


class SkillListResponse(BaseModel):
    """技能列表响应"""
    skills: List[SkillListItem]
    total: int


class SkillRule(BaseModel):
    """技能规则"""
    rule_id: str
    description: str
    content: str


class SkillMetadata(BaseModel):
    """技能元数据"""
    created_at: str
    updated_at: str


class SkillDetailResponse(BaseModel):
    """技能详情响应"""
    id: str
    name: str
    description: str
    stage: str
    tags: List[str]
    rules: List[SkillRule]
    examples: List[str]
    metadata: SkillMetadata


class CreateSkillRequest(BaseModel):
    """创建技能请求"""
    name: str = Field(..., description="技能名称")
    description: str = Field(..., description="技能描述")
    stage: str = Field(..., description="适用阶段")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    rules: List[SkillRule] = Field(default_factory=list, description="规则列表")


class UpdateSkillRequest(CreateSkillRequest):
    pass


class CreateSkillResponse(BaseModel):
    """创建技能响应"""
    id: str
    path: str
    message: str


class UpdateSkillResponse(BaseModel):
    """更新技能响应"""
    id: str
    message: str


class DeleteSkillResponse(BaseModel):
    """删除技能响应"""
    message: str


class SelectSkillsRequest(BaseModel):
    """智能选择技能请求"""
    user_text: str = Field(..., description="用户意图描述")
    stage: Optional[str] = Field(default=None, description="适用阶段")
    limit: Optional[int] = Field(default=3, description="返回数量限制")


class SkillSelectionItem(BaseModel):
    """技能选择项"""
    id: str
    name: str
    relevance_score: float


class SelectSkillsResponse(BaseModel):
    """智能选择技能响应"""
    skills: List[SkillSelectionItem]
    total: int


# ==================== WebSocket Models ====================

class WSConfigMessage(BaseModel):
    """WebSocket 配置消息"""
    type: str = "config"
    data: Dict[str, Any]


class WSStatusMessage(BaseModel):
    """WebSocket 状态消息"""
    type: str = "status"
    message: str


class WSAnalysisMessage(BaseModel):
    """WebSocket 分析消息"""
    type: str = "analysis"
    data: Dict[str, Any]


class WSStopMessage(BaseModel):
    """WebSocket 停止消息"""
    type: str = "stop"


# ==================== Error Models ====================

class ErrorDetail(BaseModel):
    """错误详情"""
    code: ErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    error: ErrorDetail
    timestamp: str


# ==================== Success Response Wrapper ====================

class SuccessResponse(BaseModel):
    """成功响应包装器"""
    success: bool = True
    data: Any
    agent_type: Optional[str] = None
    timestamp: str
