"""
运行指标 Schema
"""

from pydantic import BaseModel, Field


class RunMetrics(BaseModel):
    """运行指标"""

    total_frames: int = Field(..., description="总帧数")
    selected_frames: int = Field(..., description="选中的关键帧数")
    compression_ratio: float = Field(..., description="压缩率 (0-1)")
    events_detected: int = Field(..., description="检测到的事件数")
    commands_generated: int = Field(..., description="生成的命令数")
    highlight_segments: int = Field(..., description="高光片段数")
    processing_time_sec: float = Field(..., description="处理时长（秒）")
    frames_per_second: float = Field(..., description="处理速度（帧/秒）")
