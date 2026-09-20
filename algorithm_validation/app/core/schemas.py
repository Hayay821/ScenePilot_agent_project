"""
核心数据结构定义 - 统一的 Pydantic Schema
所有模块通过这些 Schema 交换数据，确保类型安全和可序列化
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class FramePacket(BaseModel):
    """单个视频帧的数据包"""
    source_id: str = Field(..., description="视频源标识")
    frame_index: int = Field(..., ge=0, description="帧序号")
    timestamp_ms: int = Field(..., ge=0, description="时间戳（毫秒）")
    image_path: Optional[str] = Field(None, description="帧图片保存路径")
    width: int = Field(..., gt=0, description="帧宽度")
    height: int = Field(..., gt=0, description="帧高度")

    class Config:
        json_schema_extra = {
            "example": {
                "source_id": "video_001",
                "frame_index": 42,
                "timestamp_ms": 1400,
                "image_path": "keyframes/frame_042.jpg",
                "width": 1920,
                "height": 1080,
            }
        }


class SelectedFrame(BaseModel):
    """STC 选择后的关键帧"""
    frame: FramePacket
    change_score: float = Field(..., ge=0.0, le=1.0, description="变化分数")
    novelty_score: float = Field(..., ge=0.0, le=1.0, description="新颖度分数")
    selection_reason: list[str] = Field(
        default_factory=list, description="选择原因列表"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "frame": {
                    "source_id": "video_001",
                    "frame_index": 42,
                    "timestamp_ms": 1400,
                    "width": 1920,
                    "height": 1080,
                },
                "change_score": 0.75,
                "novelty_score": 0.82,
                "selection_reason": ["high_motion", "scene_change"],
            }
        }


class VideoEvent(BaseModel):
    """语义事件 - 由视觉模型识别的事件"""
    event_id: str = Field(..., description="事件唯一标识")
    start_ms: int = Field(..., ge=0, description="事件开始时间（毫秒）")
    end_ms: int = Field(..., ge=0, description="事件结束时间（毫秒）")
    event_type: str = Field(..., description="事件类型")
    description: str = Field(..., description="事件描述")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度")
    highlight_score: float = Field(..., ge=0.0, le=1.0, description="高光分数")
    key_subjects: list[str] = Field(default_factory=list, description="关键主体列表")
    camera_suggestion: str = Field(default="observe", description="相机建议")

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "evt_001",
                "start_ms": 12000,
                "end_ms": 15000,
                "event_type": "action_peak",
                "subjects": ["person_1"],
                "description": "骑马者完成跳跃动作",
                "confidence": 0.91,
                "highlight_score": 0.85,
                "evidence_frame_ids": [240, 245, 250],
            }
        }


class CameraAction(BaseModel):
    """设备命令 - 导演状态机输出的受约束命令"""
    action_id: str = Field(..., description="命令唯一标识")
    action_type: str = Field(..., description="动作类型")
    timestamp_ms: int = Field(..., description="命令生成时间戳")
    params: dict = Field(default_factory=dict, description="动作参数")

    class Config:
        json_schema_extra = {
            "example": {
                "action_id": "action_001",
                "action_type": "start_tracking",
                "timestamp_ms": 12500,
                "params": {"subject_id": "person_1"},
            }
        }


class RunMetrics(BaseModel):
    """运行指标 - 用于评估系统性能"""
    total_frames: int = Field(..., description="总帧数")
    selected_frames: int = Field(..., description="选中的关键帧数")
    compression_ratio: float = Field(..., description="压缩率 (0-1)")
    events_detected: int = Field(..., description="检测到的事件数")
    commands_generated: int = Field(..., description="生成的命令数")
    highlight_segments: int = Field(..., description="高光片段数")
    processing_time_sec: float = Field(..., description="处理时长（秒）")
    frames_per_second: float = Field(..., description="处理速度（帧/秒）")

    class Config:
        json_schema_extra = {
            "example": {
                "total_frames": 3600,
                "selected_frames": 240,
                "compression_ratio": 0.933,
                "events_detected": 12,
                "commands_generated": 15,
                "highlight_segments": 3,
                "processing_time_sec": 45.2,
                "frames_per_second": 79.6,
            }
        }


class AnalysisRequest(BaseModel):
    """分析请求"""
    video_path: str = Field(..., description="视频文件路径")
    user_intent: str = Field(..., description="用户拍摄意图")
    use_mock: bool = Field(default=False, description="是否使用Mock模式")
    realtime: bool = Field(default=False, description="是否模拟实时播放")


class AnalysisResult(BaseModel):
    """分析结果"""
    session_id: str
    events: list[VideoEvent]
    commands: list[CameraAction]
    metrics: RunMetrics
    output_paths: dict[str, str] = Field(
        default_factory=dict, description="输出文件路径映射"
    )
