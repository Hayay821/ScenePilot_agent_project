"""
X4 Air 全景相机适配器

封装 x4air_bridge C++ 服务，提供 Python 接口
"""

from typing import Optional, Dict, Any, List
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
    RecordingCapability,
)


class X4AirAdapter(DeviceAdapter):
    """
    X4 Air 设备适配器

    连接到 x4air_bridge C++ 服务 (默认 localhost:8001)
    """

    def __init__(
        self,
        bridge_url: str = "http://localhost:8001",
        device_id: Optional[str] = None,
        timeout_sec: int = 10,  # X4 Air 操作可能较慢
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

        # 录制状态
        self._is_recording = False
        self._current_file: Optional[str] = None

    async def connect(self) -> bool:
        """连接 X4 Air 设备"""
        logger.info(f"X4AirAdapter: Connecting to bridge {self.bridge_url}")

        try:
            # 查询设备能力（同时验证连接）
            capabilities = await self.get_capabilities(force_refresh=True)
            self.device_id = capabilities.device_id
            self._is_connected = True
            logger.info(f"X4AirAdapter: Connected to {self.device_id}")
            return True

        except Exception as e:
            logger.error(f"X4AirAdapter: Connection failed: {e}")
            self._is_connected = False
            return False

    async def disconnect(self) -> bool:
        """断开 X4 Air 设备"""
        logger.info("X4AirAdapter: Disconnecting")

        try:
            # 如果正在录制，先停止
            if self._is_recording:
                logger.warning("X4AirAdapter: Still recording, stopping before disconnect")
                await self.stop_recording()

            self._is_connected = False
            logger.info("X4AirAdapter: Disconnected")
            return True

        except Exception as e:
            logger.error(f"X4AirAdapter: Disconnection failed: {e}")
            return False

    async def get_capabilities(self, force_refresh: bool = False) -> DeviceCapabilities:
        """查询 X4 Air 设备能力"""
        if self._capabilities and not force_refresh and self.enable_cache:
            logger.debug("X4AirAdapter: Returning cached capabilities")
            return self._capabilities

        logger.info("X4AirAdapter: Querying capabilities")

        try:
            async def _get():
                return await self._http_get("/v1/capabilities")

            data = await self._retry_with_backoff(_get)

            # 解析能力响应
            self._capabilities = DeviceCapabilities(
                device_id=data.get("device_id", "x4air-unknown"),
                device_type=DeviceType.X4_AIR,
                firmware_version=data.get("firmware_version"),
                serial_number=data.get("serial_number"),
                video=VideoCapability(
                    resolutions=data.get("capabilities", {}).get("resolutions", []),
                    frame_rates=data.get("capabilities", {}).get("frame_rates", []),
                    formats=data.get("capabilities", {}).get("formats", ["insv"]),
                ),
                recording=RecordingCapability(
                    local_recording=True,
                    remote_control=data.get("capabilities", {}).get("remote_control", True),
                    file_download=data.get("capabilities", {}).get("file_download", False),
                    preview_stream=data.get("capabilities", {}).get("preview_stream", True),
                ),
                gesture_control=False,
                audio_control=False,
                extra=data.get("capabilities", {}),
            )

            logger.info(f"X4AirAdapter: Capabilities loaded for {self._capabilities.device_id}")
            return self._capabilities

        except Exception as e:
            logger.error(f"X4AirAdapter: Failed to get capabilities: {e}")
            raise

    async def execute_command(self, command: DeviceCommand) -> CommandResult:
        """执行 X4 Air 命令"""
        if self._circuit_breaker_open:
            logger.warning("X4AirAdapter: Circuit breaker open, command rejected")
            return CommandResult(
                command_id=command.command_id,
                status=CommandStatus.FAILED,
                error="Circuit breaker open",
            )

        logger.debug(f"X4AirAdapter: Executing command {command.action}")

        try:
            async def _execute():
                return await self._http_post(
                    "/v1/commands",
                    json_data=command.model_dump(),
                )

            result_data = await self._retry_with_backoff(_execute)

            result = CommandResult(**result_data)

            # 更新内部状态
            if result.status == CommandStatus.SUCCESS:
                if command.action == CommandAction.START_RECORDING:
                    self._is_recording = True
                    self._current_file = result.result.get("file_path") if result.result else None
                elif command.action == CommandAction.STOP_RECORDING:
                    self._is_recording = False

            logger.debug(f"X4AirAdapter: Command {command.action} -> {result.status}")
            return result

        except Exception as e:
            logger.error(f"X4AirAdapter: Command execution failed: {e}")
            return CommandResult(
                command_id=command.command_id,
                status=CommandStatus.FAILED,
                error=str(e),
            )

    async def subscribe_events(self, callback):
        """订阅 X4 Air 事件流"""
        import websockets

        ws_url = self.bridge_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_url}/v1/events"

        logger.info(f"X4AirAdapter: Subscribing to events at {ws_url}")

        try:
            async with websockets.connect(ws_url) as websocket:
                logger.info("X4AirAdapter: WebSocket connected")

                async for message in websocket:
                    try:
                        import json
                        event_data = json.loads(message)
                        event = DeviceEvent(**event_data)

                        # 更新内部状态
                        if event.event_type == "recording_started":
                            self._is_recording = True
                        elif event.event_type == "recording_stopped":
                            self._is_recording = False

                        await callback(event)
                    except Exception as e:
                        logger.error(f"X4AirAdapter: Event parsing failed: {e}")

        except Exception as e:
            logger.error(f"X4AirAdapter: WebSocket error: {e}")

    # === 命令快捷方法 ===

    async def start_recording(self, **kwargs) -> CommandResult:
        """开始录制"""
        command = DeviceCommand(
            command_id=f"rec_start_{asyncio.get_event_loop().time()}",
            action=CommandAction.START_RECORDING,
            args=kwargs,
            deadline_ms=5000,  # 录制操作可能需要更长时间
        )
        return await self.execute_command(command)

    async def stop_recording(self) -> CommandResult:
        """停止录制"""
        command = DeviceCommand(
            command_id=f"rec_stop_{asyncio.get_event_loop().time()}",
            action=CommandAction.STOP_RECORDING,
            args={},
            deadline_ms=5000,
        )
        return await self.execute_command(command)

    async def start_preview(self) -> CommandResult:
        """开始预览"""
        command = DeviceCommand(
            command_id=f"preview_start_{asyncio.get_event_loop().time()}",
            action=CommandAction.START_PREVIEW,
            args={},
        )
        return await self.execute_command(command)

    async def stop_preview(self) -> CommandResult:
        """停止预览"""
        command = DeviceCommand(
            command_id=f"preview_stop_{asyncio.get_event_loop().time()}",
            action=CommandAction.STOP_PREVIEW,
            args={},
        )
        return await self.execute_command(command)

    async def list_files(self) -> List[Dict[str, Any]]:
        """列出文件"""
        command = DeviceCommand(
            command_id=f"list_files_{asyncio.get_event_loop().time()}",
            action=CommandAction.LIST_FILES,
            args={},
        )
        result = await self.execute_command(command)

        if result.status == CommandStatus.SUCCESS and result.result:
            return result.result.get("files", [])
        return []

    async def download_file(self, file_path: str, local_path: str) -> CommandResult:
        """下载文件"""
        command = DeviceCommand(
            command_id=f"download_{asyncio.get_event_loop().time()}",
            action=CommandAction.DOWNLOAD_FILE,
            args={"file_path": file_path, "local_path": local_path},
            deadline_ms=60000,  # 下载可能需要很长时间
        )
        return await self.execute_command(command)

    @property
    def is_recording(self) -> bool:
        """是否正在录制"""
        return self._is_recording

    @property
    def current_file(self) -> Optional[str]:
        """当前录制文件路径"""
        return self._current_file

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
