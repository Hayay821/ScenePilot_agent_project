"""
测试设备协议定义
"""

import pytest
from datetime import datetime
from protocols import (
    DeviceCapabilities,
    DeviceCommand,
    CommandResult,
    CommandAction,
    CommandStatus,
    DeviceEvent,
    EventType,
)
from protocols.capabilities import DeviceType, PTZCapability


def test_device_command():
    """测试设备命令"""
    command = DeviceCommand(
        command_id="test-001",
        action=CommandAction.SET_PAN_TILT_ABSOLUTE,
        args={"pan_deg": 20.0, "tilt_deg": 5.0},
        deadline_ms=1000,
    )

    assert command.command_id == "test-001"
    assert command.action == CommandAction.SET_PAN_TILT_ABSOLUTE
    assert command.args["pan_deg"] == 20.0
    assert command.deadline_ms == 1000


def test_command_result():
    """测试命令结果"""
    result = CommandResult(
        command_id="test-001",
        status=CommandStatus.SUCCESS,
        result={"pan_actual": 20.1},
        execution_time_ms=156.3,
    )

    assert result.command_id == "test-001"
    assert result.status == CommandStatus.SUCCESS
    assert result.result["pan_actual"] == 20.1
    assert result.execution_time_ms == 156.3


def test_device_event():
    """测试设备事件"""
    event = DeviceEvent(
        event_id="evt-001",
        device_id="link2-serial-123",
        event_type=EventType.PTZ_POSITION_CHANGED,
        data={"pan_deg": 20.0, "tilt_deg": 5.0},
        severity="info",
        message="PTZ position changed",
    )

    assert event.event_id == "evt-001"
    assert event.device_id == "link2-serial-123"
    assert event.event_type == EventType.PTZ_POSITION_CHANGED
    assert event.data["pan_deg"] == 20.0


def test_device_capabilities():
    """测试设备能力"""
    capabilities = DeviceCapabilities(
        device_id="link2-serial-123",
        device_type=DeviceType.LINK2,
        firmware_version="1.2.3",
        serial_number="LINK2123456",
        ptz=PTZCapability(
            pan_range=(-145.0, 145.0),
            tilt_range=(-45.0, 90.0),
            absolute_positioning=True,
        ),
        gesture_control=True,
        audio_control=True,
    )

    assert capabilities.device_id == "link2-serial-123"
    assert capabilities.device_type == DeviceType.LINK2
    assert capabilities.ptz.absolute_positioning
    assert capabilities.gesture_control


def test_command_serialization():
    """测试命令序列化"""
    command = DeviceCommand(
        command_id="test-001",
        action=CommandAction.START_TRACKING,
        args={"target_id": "person_01"},
    )

    # 转换为字典
    data = command.model_dump()

    assert data["command_id"] == "test-001"
    assert data["action"] == "start_tracking"
    assert data["args"]["target_id"] == "person_01"

    # 从字典重建
    command2 = DeviceCommand(**data)
    assert command2.command_id == command.command_id
    assert command2.action == command.action


def test_event_serialization():
    """测试事件序列化"""
    event = DeviceEvent(
        event_id="evt-001",
        device_id="x4air-serial-456",
        event_type=EventType.RECORDING_STARTED,
        data={"file_path": "/recordings/video_001.mp4"},
    )

    # 转换为字典
    data = event.model_dump()

    assert data["event_id"] == "evt-001"
    assert data["event_type"] == "recording_started"

    # 从字典重建
    event2 = DeviceEvent(**data)
    assert event2.event_id == event.event_id
    assert event2.event_type == event.event_type


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
