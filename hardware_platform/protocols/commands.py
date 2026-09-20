"""
设备命令提交协议

POST /v1/commands -> CommandResult
"""

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class CommandAction(str, Enum):
    """命令动作类型"""
    # PTZ 控制
    SET_PAN_TILT_ABSOLUTE = "set_pan_tilt_absolute"
    SET_PAN_TILT_RELATIVE = "set_pan_tilt_relative"
    PTZ_STOP = "ptz_stop"
    PTZ_HOME = "ptz_home"

    # 追踪控制
    START_TRACKING = "start_tracking"
    STOP_TRACKING = "stop_tracking"
    SET_TRACK_TARGET = "set_track_target"
    SET_TRACK_SPEED = "set_track_speed"
    SET_COMPOSITION_STYLE = "set_composition_style"

    # 录制控制
    START_RECORDING = "start_recording"
    STOP_RECORDING = "stop_recording"
    TAKE_PHOTO = "take_photo"

    # 预览控制
    START_PREVIEW = "start_preview"
    STOP_PREVIEW = "stop_preview"

    # 文件管理
    LIST_FILES = "list_files"
    DOWNLOAD_FILE = "download_file"
    DELETE_FILE = "delete_file"

    # 设置
    SET_VIDEO_MODE = "set_video_mode"
    SET_EXPOSURE = "set_exposure"
    SET_FOCUS = "set_focus"
    SET_ZOOM = "set_zoom"

    # 手势控制
    ENABLE_GESTURE = "enable_gesture"
    DISABLE_GESTURE = "disable_gesture"


class CommandStatus(str, Enum):
    """命令执行状态"""
    SUCCESS = "success"           # 成功
    FAILED = "failed"             # 失败
    TIMEOUT = "timeout"           # 超时
    UNSUPPORTED = "unsupported"   # 不支持
    INVALID_ARGS = "invalid_args" # 参数错误


class DeviceCommand(BaseModel):
    """设备命令请求"""
    command_id: str = Field(..., description="命令唯一标识")
    action: CommandAction = Field(..., description="命令动作")
    args: Dict[str, Any] = Field(
        default_factory=dict,
        description="命令参数"
    )
    deadline_ms: Optional[int] = Field(
        1000,
        description="命令超时时间（毫秒）"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "command_id": "cmd-001",
                    "action": "set_pan_tilt_absolute",
                    "args": {"pan_deg": 20.0, "tilt_deg": 5.0},
                    "deadline_ms": 1000
                },
                {
                    "command_id": "cmd-002",
                    "action": "start_tracking",
                    "args": {"target_id": "person_01"},
                    "deadline_ms": 500
                }
            ]
        }


class CommandResult(BaseModel):
    """命令执行结果"""
    command_id: str = Field(..., description="命令唯一标识")
    status: CommandStatus = Field(..., description="执行状态")
    result: Optional[Dict[str, Any]] = Field(
        None,
        description="执行结果数据"
    )
    error: Optional[str] = Field(
        None,
        description="错误信息"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="执行时间戳"
    )
    execution_time_ms: Optional[float] = Field(
        None,
        description="执行耗时（毫秒）"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "command_id": "cmd-001",
                    "status": "success",
                    "result": {"pan_actual": 20.1, "tilt_actual": 5.0},
                    "error": None,
                    "timestamp": "2024-03-20T10:30:00Z",
                    "execution_time_ms": 156.3
                },
                {
                    "command_id": "cmd-002",
                    "status": "failed",
                    "result": None,
                    "error": "Target not found",
                    "timestamp": "2024-03-20T10:30:01Z",
                    "execution_time_ms": 89.2
                }
            ]
        }


# PTZ 命令参数类型定义
class PanTiltAbsoluteArgs(BaseModel):
    """绝对位置控制参数"""
    pan_deg: float = Field(..., description="Pan 角度（度）")
    tilt_deg: float = Field(..., description="Tilt 角度（度）")
    pan_speed: Optional[float] = Field(None, description="Pan 速度")
    tilt_speed: Optional[float] = Field(None, description="Tilt 速度")


class PanTiltRelativeArgs(BaseModel):
    """相对位置控制参数"""
    pan_delta: float = Field(..., description="Pan 增量（度）")
    tilt_delta: float = Field(..., description="Tilt 增量（度）")


class TrackTargetArgs(BaseModel):
    """追踪目标参数"""
    target_id: str = Field(..., description="目标 ID")
    track_speed: Optional[str] = Field("normal", description="追踪速度")
    composition_style: Optional[str] = Field("half_body", description="构图风格")


class RecordingArgs(BaseModel):
    """录制参数"""
    resolution: Optional[tuple[int, int]] = Field(None, description="分辨率")
    frame_rate: Optional[int] = Field(None, description="帧率")
    format: Optional[str] = Field(None, description="格式")
