"""
边缘代理 - 现场电脑运行的本地控制节点

职责:
1. 管理本地设备 (Link 2 + X4 Air)
2. 本地检测跟踪和高频 PTZ 闭环
3. STC 压缩和关键帧上传
4. 断网 resilience (本地 outbox 队列)
"""

import asyncio
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
from loguru import logger

from adapters import Link2Adapter, X4AirAdapter
from protocols import DeviceEvent


class EdgeAgent:
    """
    边缘代理

    本地运行，负责:
    - 设备管理
    - 本地 PTZ 控制闭环
    - 关键帧采集和上传
    - 事件队列和断网恢复
    """

    def __init__(
        self,
        link2_bridge_url: str = "http://localhost:8002",
        x4air_bridge_url: str = "http://localhost:8001",
        cloud_endpoint: Optional[str] = None,
        local_mode: bool = False,
        outbox_dir: Optional[Path] = None,
    ):
        """
        Args:
            link2_bridge_url: Link 2 桥服务地址
            x4air_bridge_url: X4 Air 桥服务地址
            cloud_endpoint: 云端服务地址
            local_mode: 是否仅本地模式（不连云端）
            outbox_dir: 断网时事件队列目录
        """
        self.link2_adapter = Link2Adapter(bridge_url=link2_bridge_url)
        self.x4air_adapter = X4AirAdapter(bridge_url=x4air_bridge_url)

        self.cloud_endpoint = cloud_endpoint
        self.local_mode = local_mode

        self.outbox_dir = outbox_dir or Path("./data/outbox")
        self.outbox_dir.mkdir(parents=True, exist_ok=True)

        # 状态
        self._running = False
        self._cloud_connected = False
        self._event_queue: asyncio.Queue = asyncio.Queue()

        logger.info(
            f"EdgeAgent initialized: link2={link2_bridge_url}, "
            f"x4air={x4air_bridge_url}, cloud={cloud_endpoint}, "
            f"local_mode={local_mode}"
        )

    async def start(self):
        """启动边缘代理"""
        logger.info("EdgeAgent: Starting")

        # 连接设备
        link2_ok = await self.link2_adapter.connect()
        x4air_ok = await self.x4air_adapter.connect()

        if not link2_ok:
            logger.warning("EdgeAgent: Link 2 not available")

        if not x4air_ok:
            logger.warning("EdgeAgent: X4 Air not available")

        if not link2_ok and not x4air_ok:
            raise RuntimeError("EdgeAgent: No devices available")

        # 订阅设备事件
        asyncio.create_task(self._subscribe_link2_events())
        asyncio.create_task(self._subscribe_x4air_events())

        # 启动事件处理循环
        asyncio.create_task(self._event_loop())

        # 启动云端同步（如果不是本地模式）
        if not self.local_mode and self.cloud_endpoint:
            asyncio.create_task(self._cloud_sync_loop())

        self._running = True
        logger.info("EdgeAgent: Started")

    async def stop(self):
        """停止边缘代理"""
        logger.info("EdgeAgent: Stopping")
        self._running = False

        # 断开设备
        await self.link2_adapter.disconnect()
        await self.x4air_adapter.disconnect()

        logger.info("EdgeAgent: Stopped")

    # === 设备事件订阅 ===

    async def _subscribe_link2_events(self):
        """订阅 Link 2 事件"""
        async def callback(event: DeviceEvent):
            await self._event_queue.put(("link2", event))

        try:
            await self.link2_adapter.subscribe_events(callback)
        except Exception as e:
            logger.error(f"EdgeAgent: Link 2 event subscription failed: {e}")

    async def _subscribe_x4air_events(self):
        """订阅 X4 Air 事件"""
        async def callback(event: DeviceEvent):
            await self._event_queue.put(("x4air", event))

        try:
            await self.x4air_adapter.subscribe_events(callback)
        except Exception as e:
            logger.error(f"EdgeAgent: X4 Air event subscription failed: {e}")

    # === 事件处理循环 ===

    async def _event_loop(self):
        """事件处理主循环"""
        logger.info("EdgeAgent: Event loop started")

        while self._running:
            try:
                # 从队列获取事件
                source, event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0
                )

                logger.debug(f"EdgeAgent: Event from {source}: {event.event_type}")

                # 处理事件
                await self._handle_event(source, event)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"EdgeAgent: Event handling error: {e}")

        logger.info("EdgeAgent: Event loop stopped")

    async def _handle_event(self, source: str, event: DeviceEvent):
        """
        处理设备事件

        Args:
            source: 事件来源 ("link2" 或 "x4air")
            event: 设备事件
        """
        # 本地处理
        if event.event_type == "target_lost":
            logger.warning(f"EdgeAgent: Target lost on {source}, stopping tracking")
            if source == "link2":
                await self.link2_adapter.stop_tracking()

        elif event.event_type == "ptz_limit_reached":
            logger.warning(f"EdgeAgent: PTZ limit reached on {source}")
            if source == "link2":
                await self.link2_adapter.ptz_stop()

        # 上传到云端（如果连接）
        if self._cloud_connected and not self.local_mode:
            await self._upload_event(event)
        else:
            # 断网时写入 outbox
            await self._write_to_outbox(event)

    # === 云端同步 ===

    async def _cloud_sync_loop(self):
        """云端同步循环"""
        logger.info("EdgeAgent: Cloud sync loop started")

        while self._running:
            try:
                # 检查云端连接
                await self._check_cloud_connection()

                # 如果连接，同步 outbox
                if self._cloud_connected:
                    await self._sync_outbox()

                await asyncio.sleep(5.0)  # 每 5 秒检查一次

            except Exception as e:
                logger.error(f"EdgeAgent: Cloud sync error: {e}")
                self._cloud_connected = False
                await asyncio.sleep(10.0)

        logger.info("EdgeAgent: Cloud sync loop stopped")

    async def _check_cloud_connection(self):
        """检查云端连接"""
        if not self.cloud_endpoint:
            self._cloud_connected = False
            return

        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.cloud_endpoint}/health")
                self._cloud_connected = response.status_code == 200

        except Exception as e:
            logger.debug(f"EdgeAgent: Cloud not reachable: {e}")
            self._cloud_connected = False

    async def _upload_event(self, event: DeviceEvent):
        """上传事件到云端"""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.cloud_endpoint}/v1/events",
                    json=event.model_dump(),
                )
                response.raise_for_status()
                logger.debug(f"EdgeAgent: Event uploaded: {event.event_id}")

        except Exception as e:
            logger.warning(f"EdgeAgent: Failed to upload event: {e}")
            # 上传失败，写入 outbox
            await self._write_to_outbox(event)

    async def _write_to_outbox(self, event: DeviceEvent):
        """写入事件到本地 outbox"""
        try:
            import json
            outbox_file = self.outbox_dir / f"{event.event_id}.json"
            with open(outbox_file, "w") as f:
                json.dump(event.model_dump(), f, indent=2)

            logger.debug(f"EdgeAgent: Event saved to outbox: {outbox_file}")

        except Exception as e:
            logger.error(f"EdgeAgent: Failed to write outbox: {e}")

    async def _sync_outbox(self):
        """同步 outbox 中的事件到云端"""
        if not self._cloud_connected:
            return

        import json
        outbox_files = sorted(self.outbox_dir.glob("*.json"))

        if not outbox_files:
            return

        logger.info(f"EdgeAgent: Syncing {len(outbox_files)} events from outbox")

        for outbox_file in outbox_files:
            try:
                with open(outbox_file, "r") as f:
                    event_data = json.load(f)

                # 上传
                import httpx
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        f"{self.cloud_endpoint}/v1/events",
                        json=event_data,
                    )
                    response.raise_for_status()

                # 删除已同步的文件
                outbox_file.unlink()
                logger.debug(f"EdgeAgent: Synced and removed: {outbox_file}")

            except Exception as e:
                logger.warning(f"EdgeAgent: Failed to sync {outbox_file}: {e}")
                break  # 停止同步，等下次重试

    # === 本地控制接口 ===

    async def set_pan_tilt(self, pan_deg: float, tilt_deg: float):
        """本地 PTZ 控制"""
        return await self.link2_adapter.set_pan_tilt(pan_deg, tilt_deg)

    async def start_tracking(self, target_id: Optional[str] = None):
        """开始追踪"""
        return await self.link2_adapter.start_tracking(target_id)

    async def start_recording(self):
        """开始录制"""
        return await self.x4air_adapter.start_recording()

    async def stop_recording(self):
        """停止录制"""
        return await self.x4air_adapter.stop_recording()

    # === 状态查询 ===

    @property
    def is_link2_available(self) -> bool:
        """Link 2 是否可用"""
        return self.link2_adapter.is_available

    @property
    def is_x4air_available(self) -> bool:
        """X4 Air 是否可用"""
        return self.x4air_adapter.is_available

    @property
    def is_cloud_connected(self) -> bool:
        """云端是否连接"""
        return self._cloud_connected
