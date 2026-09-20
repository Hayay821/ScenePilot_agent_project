"""
测试 Link 2 适配器
"""

import pytest
import asyncio
from adapters import Link2Adapter
from protocols import DeviceCommand, CommandAction, CommandStatus


@pytest.fixture
def link2_adapter():
    """创建 Link 2 适配器实例"""
    return Link2Adapter(
        bridge_url="http://localhost:8002",
        timeout_sec=5,
        max_retries=1,
    )


@pytest.mark.asyncio
async def test_connection(link2_adapter):
    """测试设备连接"""
    # 注意: 需要 link2_bridge 服务运行
    connected = await link2_adapter.connect()

    if connected:
        assert link2_adapter.is_connected
        assert link2_adapter.device_id is not None

        # 断开连接
        disconnected = await link2_adapter.disconnect()
        assert disconnected
        assert not link2_adapter.is_connected


@pytest.mark.asyncio
async def test_get_capabilities(link2_adapter):
    """测试获取设备能力"""
    await link2_adapter.connect()

    capabilities = await link2_adapter.get_capabilities()

    assert capabilities.device_id is not None
    assert capabilities.device_type == "link2"

    # PTZ 能力
    assert capabilities.ptz is not None
    assert capabilities.ptz.absolute_positioning

    await link2_adapter.disconnect()


@pytest.mark.asyncio
async def test_ptz_command(link2_adapter):
    """测试 PTZ 控制命令"""
    await link2_adapter.connect()

    # 发送 PTZ 命令
    result = await link2_adapter.set_pan_tilt(0.0, 0.0)

    assert result.command_id is not None
    assert result.status in [CommandStatus.SUCCESS, CommandStatus.FAILED]

    # 停止 PTZ
    stop_result = await link2_adapter.ptz_stop()
    assert stop_result.command_id is not None

    await link2_adapter.disconnect()


@pytest.mark.asyncio
async def test_circuit_breaker(link2_adapter):
    """测试熔断器"""
    # 使用错误的 URL 触发失败
    bad_adapter = Link2Adapter(
        bridge_url="http://localhost:9999",
        timeout_sec=1,
        max_retries=1,
    )

    # 多次失败应该打开熔断器
    for _ in range(6):
        try:
            await bad_adapter.connect()
        except:
            pass

    assert bad_adapter._circuit_breaker_open

    # 重置熔断器
    bad_adapter.reset_circuit_breaker()
    assert not bad_adapter._circuit_breaker_open


@pytest.mark.asyncio
async def test_capability_cache(link2_adapter):
    """测试能力缓存"""
    await link2_adapter.connect()

    # 第一次查询
    cap1 = await link2_adapter.get_capabilities()

    # 第二次应该从缓存返回
    cap2 = await link2_adapter.get_capabilities()

    assert cap1.device_id == cap2.device_id

    # 强制刷新
    cap3 = await link2_adapter.get_capabilities(force_refresh=True)

    assert cap3.device_id == cap1.device_id

    await link2_adapter.disconnect()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
