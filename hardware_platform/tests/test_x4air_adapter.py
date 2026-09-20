"""
测试 X4 Air 适配器
"""

import pytest
import asyncio
from adapters import X4AirAdapter
from protocols import DeviceCommand, CommandAction, CommandStatus


@pytest.fixture
def x4air_adapter():
    """创建 X4 Air 适配器实例"""
    return X4AirAdapter(
        bridge_url="http://localhost:8001",
        timeout_sec=10,
        max_retries=1,
    )


@pytest.mark.asyncio
async def test_connection(x4air_adapter):
    """测试设备连接"""
    # 注意: 需要 x4air_bridge 服务运行
    connected = await x4air_adapter.connect()

    if connected:
        assert x4air_adapter.is_connected
        assert x4air_adapter.device_id is not None

        # 断开连接
        disconnected = await x4air_adapter.disconnect()
        assert disconnected
        assert not x4air_adapter.is_connected


@pytest.mark.asyncio
async def test_get_capabilities(x4air_adapter):
    """测试获取设备能力"""
    await x4air_adapter.connect()

    capabilities = await x4air_adapter.get_capabilities()

    assert capabilities.device_id is not None
    assert capabilities.device_type == "x4_air"

    # 录制能力
    assert capabilities.recording is not None
    assert capabilities.recording.local_recording

    await x4air_adapter.disconnect()


@pytest.mark.asyncio
async def test_recording_commands(x4air_adapter):
    """测试录制命令"""
    await x4air_adapter.connect()

    # 开始录制
    start_result = await x4air_adapter.start_recording()

    assert start_result.command_id is not None

    if start_result.status == CommandStatus.SUCCESS:
        assert x4air_adapter.is_recording

        # 等待一会
        await asyncio.sleep(2)

        # 停止录制
        stop_result = await x4air_adapter.stop_recording()
        assert stop_result.command_id is not None

        if stop_result.status == CommandStatus.SUCCESS:
            assert not x4air_adapter.is_recording

    await x4air_adapter.disconnect()


@pytest.mark.asyncio
async def test_list_files(x4air_adapter):
    """测试文件列表"""
    await x4air_adapter.connect()

    files = await x4air_adapter.list_files()

    # 应该返回列表（可能为空）
    assert isinstance(files, list)

    await x4air_adapter.disconnect()


@pytest.mark.asyncio
async def test_preview_commands(x4air_adapter):
    """测试预览命令"""
    await x4air_adapter.connect()

    # 开始预览
    start_result = await x4air_adapter.start_preview()
    assert start_result.command_id is not None

    # 停止预览
    stop_result = await x4air_adapter.stop_preview()
    assert stop_result.command_id is not None

    await x4air_adapter.disconnect()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
