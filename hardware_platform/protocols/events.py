"""
设备事件流协议

WebSocket /v1/events -> DeviceEvent (stream)
"""

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class EventType(str, Enum):
    """事件类型"""
    # 连接事件
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTION_ERROR = "connection_error"

    # 录制事件
    RECORDING_STARTED = "recording_started"
    RECORDING_STOPPED = "recording_stopped"
    RECORDING_ERROR = "recording_error"
    FILE_SAVED = "file_saved"

    # 追踪事件
    TRACKING_STARTED = "tracking_started"
    TRACKING_STOPPED = "tracking_stopped"
    TARGET_LOST = "target_lost"
    TARGET_ACQUIRED = "target_acquired"

    # 设备状态
    BATTERY_LOW = "battery_low"
    STORAGE_LOW = "storage_low"
    TEMPERATURE_WARNING = "temperature_warning"
    FIRMWARE_UPDATE_AVAILABLE = "firmware_update_available"

    # PTZ 事件
    PTZ_POSITION_CHANGED = "ptz_position_changed"
    PTZ_LIMIT_REACHED = "ptz_limit_reached"

    # 手势事件
    GESTURE_DETECTED = "gesture_detected"

    # 系统事件
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ConnectionState(str, Enum):
    """连接状态"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    ERROR = "error"


class DeviceEvent(BaseModel):
    """设备事件"""
    event_id: str = Field(..., description="事件唯一标识")
    device_id: str = Field(..., description="设备 ID")
    event_type: EventType = Field(..., description="事件类型")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="事件时间戳"
    )
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="事件数据"
    )
    severity: str = Field(
        default="info",
        description="严重程度: info/warning/error"
    )
    message: Optional[str] = Field(
        None,
        description="事件描述"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "event_id": "evt-001",
                    "device_id": "link2-serial-123",
                    "event_type": "recording_started",
                    "timestamp": "2024-03-20T10:30:00Z",
                    "data": {"file_path": "/recordings/video_001.mp4"},
                    "severity": "info",
                    "message": "Recording started"
                },
                {
                    "event_id": "evt-002",
                    "device_id": "x4air-serial-456",
                    "event_type": "temperature_warning",
                    "timestamp": "2024-03-20T10:35:00Z",
                    "data": {"temperature_celsius": 65.5},
                    "severity": "warning",
                    "message": "Device temperature high"
                }
            ]
        }


# 特定事件数据类型
class ConnectionEventData(BaseModel):
    """连接事件数据"""
    connection_state: ConnectionState
    device_info: Optional[Dict[str, Any]] = None


class RecordingEventData(BaseModel):
    """录制事件数据"""
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    duration_ms: Optional[int] = None


class TrackingEventData(BaseModel):
    """追踪事件数据"""
    target_id: Optional[str] = None
    confidence: Optional[float] = None
    bbox: Optional[tuple[int, int, int, int]] = None  # x, y, w, h


class PTZEventData(BaseModel):
    """PTZ 事件数据"""
    pan_deg: float
    tilt_deg: float
    zoom_level: Optional[float] = None


class GestureEventData(BaseModel):
    """手势事件数据"""
    gesture_type: str  # "palm", "l", "v", etc.
    confidence: float
