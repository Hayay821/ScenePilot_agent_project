"""
统一设备协议定义

所有设备桥遵循相同的协议接口：
- 能力查询 (capabilities)
- 命令提交 (commands)
- 事件流 (events)
"""

from .capabilities import DeviceCapabilities, CapabilityQuery
from .commands import DeviceCommand, CommandResult, CommandStatus
from .events import DeviceEvent, EventType, ConnectionState

__all__ = [
    "DeviceCapabilities",
    "CapabilityQuery",
    "DeviceCommand",
    "CommandResult",
    "CommandStatus",
    "DeviceEvent",
    "EventType",
    "ConnectionState",
]
