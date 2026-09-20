"""
设备能力查询协议

GET /v1/capabilities -> DeviceCapabilities
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DeviceType(str, Enum):
    """设备类型"""
    LINK2 = "link2"
    X4_AIR = "x4_air"
    MOCK = "mock"


class VideoCapability(BaseModel):
    """视频能力"""
    resolutions: List[tuple[int, int]] = Field(
        default_factory=list,
        description="支持的分辨率列表 [(width, height)]"
    )
    frame_rates: List[int] = Field(
        default_factory=list,
        description="支持的帧率列表"
    )
    formats: List[str] = Field(
        default_factory=list,
        description="支持的视频格式 ['h264', 'h265', 'mjpeg']"
    )


class PTZCapability(BaseModel):
    """云台能力"""
    pan_range: tuple[float, float] = Field(
        default=(-145.0, 145.0),
        description="Pan 范围（度）"
    )
    tilt_range: tuple[float, float] = Field(
        default=(-45.0, 90.0),
        description="Tilt 范围（度）"
    )
    pan_speed_range: tuple[float, float] = Field(
        default=(1.0, 100.0),
        description="Pan 速度范围"
    )
    tilt_speed_range: tuple[float, float] = Field(
        default=(1.0, 100.0),
        description="Tilt 速度范围"
    )
    absolute_positioning: bool = Field(
        default=True,
        description="是否支持绝对位置控制"
    )
    relative_positioning: bool = Field(
        default=False,
        description="是否支持相对位置控制"
    )


class TrackingCapability(BaseModel):
    """追踪能力"""
    auto_tracking: bool = Field(
        default=False,
        description="是否支持自动追踪"
    )
    target_selection: bool = Field(
        default=False,
        description="是否支持选择追踪目标"
    )
    track_speeds: List[str] = Field(
        default_factory=lambda: ["slow", "normal", "fast"],
        description="支持的追踪速度"
    )
    composition_styles: List[str] = Field(
        default_factory=list,
        description="支持的构图风格 ['head', 'half_body', 'full_body']"
    )


class RecordingCapability(BaseModel):
    """录制能力"""
    local_recording: bool = Field(
        default=False,
        description="是否支持本地录制"
    )
    remote_control: bool = Field(
        default=False,
        description="是否支持远程控制录制"
    )
    file_download: bool = Field(
        default=False,
        description="是否支持文件下载"
    )
    preview_stream: bool = Field(
        default=False,
        description="是否支持预览流"
    )


class DeviceCapabilities(BaseModel):
    """设备能力响应"""
    device_id: str = Field(..., description="设备唯一标识")
    device_type: DeviceType = Field(..., description="设备类型")
    firmware_version: Optional[str] = Field(None, description="固件版本")
    serial_number: Optional[str] = Field(None, description="序列号")

    # 各项能力
    video: Optional[VideoCapability] = Field(None, description="视频能力")
    ptz: Optional[PTZCapability] = Field(None, description="云台能力")
    tracking: Optional[TrackingCapability] = Field(None, description="追踪能力")
    recording: Optional[RecordingCapability] = Field(None, description="录制能力")

    # 其他能力
    gesture_control: bool = Field(default=False, description="是否支持手势控制")
    audio_control: bool = Field(default=False, description="是否支持音频控制")

    # 扩展字段
    extra: Dict[str, Any] = Field(
        default_factory=dict,
        description="设备特有的额外能力"
    )


class CapabilityQuery(BaseModel):
    """能力查询请求（可选，用于过滤）"""
    query_fields: Optional[List[str]] = Field(
        None,
        description="查询特定字段，None 表示返回全部"
    )
