"""
硬件平台 CLI 工具

用于测试和管理硬件设备
"""

import asyncio
import click
from loguru import logger
from pathlib import Path

from adapters import Link2Adapter, X4AirAdapter, MockAdapter
from edge import EdgeAgent


@click.group()
def cli():
    """Hardware Platform CLI - 硬件设备管理工具"""
    pass


@cli.command()
@click.option("--bridge-url", default="http://localhost:8002", help="Link 2 bridge URL")
def test_link2(bridge_url: str):
    """测试 Link 2 连接和能力"""

    async def _test():
        logger.info(f"Testing Link 2 at {bridge_url}")

        adapter = Link2Adapter(bridge_url=bridge_url)

        # 连接
        connected = await adapter.connect()
        if not connected:
            logger.error("Failed to connect to Link 2")
            return

        logger.info(f"Connected: {adapter.device_id}")

        # 获取能力
        capabilities = await adapter.get_capabilities()
        logger.info(f"Capabilities: {capabilities.model_dump_json(indent=2)}")

        # 测试 PTZ
        logger.info("Testing PTZ control...")
        result = await adapter.set_pan_tilt(0.0, 0.0)
        logger.info(f"PTZ result: {result.status}")

        await asyncio.sleep(1)

        # 停止
        await adapter.ptz_stop()

        # 断开
        await adapter.disconnect()
        logger.info("Test complete")

    asyncio.run(_test())


@cli.command()
@click.option("--bridge-url", default="http://localhost:8001", help="X4 Air bridge URL")
def test_x4air(bridge_url: str):
    """测试 X4 Air 连接和能力"""

    async def _test():
        logger.info(f"Testing X4 Air at {bridge_url}")

        adapter = X4AirAdapter(bridge_url=bridge_url)

        # 连接
        connected = await adapter.connect()
        if not connected:
            logger.error("Failed to connect to X4 Air")
            return

        logger.info(f"Connected: {adapter.device_id}")

        # 获取能力
        capabilities = await adapter.get_capabilities()
        logger.info(f"Capabilities: {capabilities.model_dump_json(indent=2)}")

        # 列出文件
        logger.info("Listing files...")
        files = await adapter.list_files()
        logger.info(f"Found {len(files)} files")

        # 断开
        await adapter.disconnect()
        logger.info("Test complete")

    asyncio.run(_test())


@cli.command()
@click.option("--link2-bridge", default="http://localhost:8002", help="Link 2 bridge URL")
@click.option("--x4air-bridge", default="http://localhost:8001", help="X4 Air bridge URL")
@click.option("--cloud-endpoint", default=None, help="Cloud service endpoint")
@click.option("--local-mode", is_flag=True, help="Run in local-only mode")
def start_edge_agent(link2_bridge: str, x4air_bridge: str, cloud_endpoint: str, local_mode: bool):
    """启动边缘代理"""

    async def _run():
        logger.info("Starting Edge Agent...")

        agent = EdgeAgent(
            link2_bridge_url=link2_bridge,
            x4air_bridge_url=x4air_bridge,
            cloud_endpoint=cloud_endpoint,
            local_mode=local_mode,
        )

        await agent.start()

        logger.info("Edge Agent running. Press Ctrl+C to stop.")

        try:
            # 保持运行
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping Edge Agent...")
            await agent.stop()

    asyncio.run(_run())


@cli.command()
def test_mock():
    """测试 Mock 适配器"""

    async def _test():
        logger.info("Testing Mock Adapter")

        adapter = MockAdapter(bridge_url="http://mock")

        # 连接
        await adapter.connect()
        logger.info(f"Connected: {adapter.device_id}")

        # 获取能力
        capabilities = await adapter.get_capabilities()
        logger.info(f"Capabilities: {capabilities.model_dump_json(indent=2)}")

        # 执行命令
        from protocols import DeviceCommand, CommandAction
        command = DeviceCommand(
            command_id="test-001",
            action=CommandAction.PTZ_STOP,
            args={},
        )

        result = await adapter.execute_command(command)
        logger.info(f"Command result: {result.status}")

        # 断开
        await adapter.disconnect()
        logger.info("Test complete")

    asyncio.run(_test())


if __name__ == "__main__":
    cli()
