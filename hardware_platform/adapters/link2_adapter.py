"""
Link 2 云台相机适配器

封装 link2_bridge C++ 服务，提供 Python 接口
"""

from typing import Optional, Dict, Any
import asyncio
from loguru import logger

from .base import DeviceAdapter
from protocols import (
    DeviceCapabilities,
    DeviceCommand,
    CommandResult,
    CommandAction,
    CommandStatus,
    DeviceEvent,
)
from protocols.capabilities import (
    DeviceType,
    VideoCapability,
    PTZCapability,
    TrackingCapability,
)


class Link2Adapter(DeviceAdapter):
    """
    Link 2 设备适配器

    连接到 link2_bridge C++ 服务 (默认 localhost:8002)
    """

    def __init__(
        self,
        bridge_url: str = "http://localhost:8002",
        device_id: Optional[str] = None,
        timeout_sec: int = 5,
        max_retries: int = 3,
        enable_cache: bool = True,
    ):
        super().__init__(
            bridge_url=bridge_url,
            device_id=device_id,
            timeout_sec=timeout_sec,
            max_retries=max_retries,
            enable_cache=enable_cache,
        )

    async def connect(self) -> bool:
        """连接 Link 2 设备"""
        logger.info(f"Link2Adapter: Connecting to bridge {self.bridge_url}")

        try:
            # 查询设备能力（同时验证连接）
            capabilities = await self.get_capabilities(force_refresh=True)
            self.device_id = capabilities.device_id
            self._is_connected = True
            logger.info(f"Link2Adapter: Connected to {self.device_id}")
            return True

        except Exception as e:
            logger.error(f"Link2Adapter: Connection failed: {e}")
            self._is_connected = False
            return False

    async def disconnect(self) -> bool:
        """断开 Link 2 设备"""
        logger.info("Link2Adapter: Disconnecting")

        try:
            # 发送 PTZ Stop 命令确保安全
            stop_command = DeviceCommand(
                command_id="disconnect_stop",
                action=CommandAction.PTZ_STOP,
                args={},
            )
            await self.execute_command(stop_command)

            self._is_connected = False
            logger.info("Link2Adapter: Disconnected")
            return True

        except Exception as e:
            logger.error(f"Link2Adapter: Disconnection failed: {e}")
            return False

    async def get_capabilities(self, force_refresh: bool = False) -> DeviceCapabilities:
        """查询 Link 2 设备能力"""
        if self._capabilities and not force_refresh and self.enable_cache:
            logger.debug("Link2Adapter: Returning cached capabilities")
            return self._capabilities

        logger.info("Link2Adapter: Querying capabilities")

        try:
            async def _get():
                return await self._http_get("/v1/capabilities")

            data = await self._retry_with_backoff(_get)

            # 解析能力响应
            self._capabilities = DeviceCapabilities(
                device_id=data.get("device_id", "link2-unknown"),
                device_type=DeviceType.LINK2,
                firmware_version=data.get("firmware_version"),
                serial_number=data.get("serial_number"),
                video=VideoCapability(
                    resolutions=data.get("capabilities", {}).get("resolutions", []),
                    frame_rates=data.get("capabilities", {}).get("frame_rates", []),
                    formats=data.get("capabilities", {}).get("formats", ["h264"]),
                ),
                ptz=PTZCapability(
                    pan_range=tuple(data.get("capabilities", {}).get("pan_range", [-145.0, 145.0])),
                    tilt_range=tuple(data.get("capabilities", {}).get("tilt_range", [-45.0, 90.0])),
                    absolute_positioning=data.get("capabilities", {}).get("pan_tilt_absolute", True),
                    relative_positioning=False,
                ),
                tracking=TrackingCapability(
                    auto_tracking=data.get("capabilities", {}).get("tracking", False),
                    target_selection=data.get("capabilities", {}).get("track_target_selection", False),
                    track_speeds=data.get("capabilities", {}).get("track_speeds", ["slow", "normal", "fast"]),
                    composition_styles=data.get("capabilities", {}).get("composition", []),
                ),
                gesture_control=data.get("capabilities", {}).get("gesture", False),
                audio_control=data.get("capabilities", {}).get("audio", False),
                extra=data.get("capabilities", {}),
            )

            logger.info(f"Link2Adapter: Capabilities loaded for {self._capabilities.device_id}")
            return self._capabilities

        except Exception as e:
            logger.error(f"Link2Adapter: Failed to get capabilities: {e}")
            raise

    async def execute_command(self, command: DeviceCommand) -> CommandResult:
        """执行 Link 2 命令"""
        if self._circuit_breaker_open:
            logger.warning("Link2Adapter: Circuit breaker open, command rejected")
            return CommandResult(
                command_id=command.command_id,
                status=CommandStatus.FAILED,
                error="Circuit breaker open",
            )

        logger.debug(f"Link2Adapter: Executing command {command.action}")

        try:
            async def _execute():
                return await self._http_post(
                    "/v1/commands",
                    json_data=command.model_dump(),
                )

            result_data = await self._retry_with_backoff(_execute)

            result = CommandResult(**result_data)
            logger.debug(f"Link2Adapter: Command {command.action} -> {result.status}")
            return result

        except Exception as e:
            logger.error(f"Link2Adapter: Command execution failed: {e}")
            return CommandResult(
                command_id=command.command_id,
                status=CommandStatus.FAILED,
                error=str(e),
            )

    async def subscribe_events(self, callback):
        """订阅 Link 2 事件流"""
        import websockets

        ws_url = self.bridge_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_url}/v1/events"

        logger.info(f"Link2Adapter: Subscribing to events at {ws_url}")

        try:
            async with websockets.connect(ws_url) as websocket:
                logger.info("Link2Adapter: WebSocket connected")

                async for message in websocket:
                    try:
                        import json
                        event_data = json.loads(message)
                        event = DeviceEvent(**event_data)
                        await callback(event)
                    except Exception as e:
                        logger.error(f"Link2Adapter: Event parsing failed: {e}")

        except Exception as e:
            logger.error(f"Link2Adapter: WebSocket error: {e}")

    # === 命令快捷方法 ===

    async def set_pan_tilt(self, pan_deg: float, tilt_deg: float) -> CommandResult:
        """设置 Pan/Tilt 绝对位置"""
        command = DeviceCommand(
            command_id=f"ptz_{asyncio.get_event_loop().time()}",
            action=CommandAction.SET_PAN_TILT_ABSOLUTE,
            args={"pan_deg": pan_deg, "tilt_deg": tilt_deg},
        )
        return await self.execute_command(command)

    async def start_tracking(self, target_id: Optional[str] = None) -> CommandResult:
        """开始追踪"""
        command = DeviceCommand(
            command_id=f"track_{asyncio.get_event_loop().time()}",
            action=CommandAction.START_TRACKING,
            args={"target_id": target_id} if target_id else {},
        )
        return await self.execute_command(command)

    async def stop_tracking(self) -> CommandResult:
        """停止追踪"""
        command = DeviceCommand(
            command_id=f"stop_track_{asyncio.get_event_loop().time()}",
            action=CommandAction.STOP_TRACKING,
            args={},
        )
        return await self.execute_command(command)

    async def ptz_stop(self) -> CommandResult:
        """PTZ 停止"""
        command = DeviceCommand(
            command_id=f"ptz_stop_{asyncio.get_event_loop().time()}",
            action=CommandAction.PTZ_STOP,
            args={},
        )
        return await self.execute_command(command)

    # === CameraAction 转换 ===

    def to_camera_action(self, command: DeviceCommand):
        """将设备命令转换为 CameraAction"""
        # TODO: 实现转换逻辑
        # 需要 algorithm_validation 的 CameraAction 定义
        raise NotImplementedError("CameraAction conversion not yet implemented")

    def from_camera_action(self, action):
        """将 CameraAction 转换为设备命令"""
        # TODO: 实现转换逻辑
        raise NotImplementedError("CameraAction conversion not yet implemented")
