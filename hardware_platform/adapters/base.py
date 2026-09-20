"""
设备适配器基类

所有设备适配器的统一接口，桥接 C++ 设备桥和 Python AI Service
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import asyncio
from loguru import logger

from protocols import DeviceCapabilities, DeviceCommand, CommandResult, DeviceEvent


class DeviceAdapter(ABC):
    """
    设备适配器抽象基类

    职责:
    1. 封装设备桥 HTTP 客户端
    2. 转换为 algorithm_validation 的 CameraAction 接口
    3. 提供能力缓存、超时重试、熔断降级
    """

    def __init__(
        self,
        bridge_url: str,
        device_id: Optional[str] = None,
        timeout_sec: int = 5,
        max_retries: int = 3,
        enable_cache: bool = True,
    ):
        """
        Args:
            bridge_url: 设备桥地址，如 http://localhost:8002
            device_id: 设备 ID，None 则自动检测
            timeout_sec: 命令超时时间（秒）
            max_retries: 最大重试次数
            enable_cache: 是否启用能力缓存
        """
        self.bridge_url = bridge_url.rstrip("/")
        self.device_id = device_id
        self.timeout_sec = timeout_sec
        self.max_retries = max_retries
        self.enable_cache = enable_cache

        # 能力缓存
        self._capabilities: Optional[DeviceCapabilities] = None
        self._is_connected = False

        # 熔断器状态
        self._circuit_breaker_failures = 0
        self._circuit_breaker_threshold = 5
        self._circuit_breaker_open = False

        logger.info(
            f"{self.__class__.__name__} initialized: bridge={bridge_url}, "
            f"timeout={timeout_sec}s, retries={max_retries}"
        )

    @abstractmethod
    async def connect(self) -> bool:
        """
        连接设备

        Returns:
            连接是否成功
        """
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """
        断开设备连接

        Returns:
            断开是否成功
        """
        pass

    @abstractmethod
    async def get_capabilities(self, force_refresh: bool = False) -> DeviceCapabilities:
        """
        查询设备能力

        Args:
            force_refresh: 是否强制刷新缓存

        Returns:
            设备能力
        """
        pass

    @abstractmethod
    async def execute_command(self, command: DeviceCommand) -> CommandResult:
        """
        执行设备命令

        Args:
            command: 设备命令

        Returns:
            命令执行结果
        """
        pass

    @abstractmethod
    async def subscribe_events(self, callback):
        """
        订阅设备事件流

        Args:
            callback: 事件回调函数 (event: DeviceEvent) -> None
        """
        pass

    # === 状态查询 ===

    @property
    def is_connected(self) -> bool:
        """设备是否已连接"""
        return self._is_connected

    @property
    def is_available(self) -> bool:
        """设备是否可用（已连接且熔断器未打开）"""
        return self._is_connected and not self._circuit_breaker_open

    # === 熔断器 ===

    def _record_success(self):
        """记录成功，重置熔断器"""
        self._circuit_breaker_failures = 0
        if self._circuit_breaker_open:
            logger.info(f"{self.__class__.__name__}: Circuit breaker closed")
            self._circuit_breaker_open = False

    def _record_failure(self):
        """记录失败，可能打开熔断器"""
        self._circuit_breaker_failures += 1
        if self._circuit_breaker_failures >= self._circuit_breaker_threshold:
            if not self._circuit_breaker_open:
                logger.error(
                    f"{self.__class__.__name__}: Circuit breaker opened "
                    f"after {self._circuit_breaker_failures} failures"
                )
                self._circuit_breaker_open = True

    def reset_circuit_breaker(self):
        """手动重置熔断器"""
        self._circuit_breaker_failures = 0
        self._circuit_breaker_open = False
        logger.info(f"{self.__class__.__name__}: Circuit breaker manually reset")

    # === 辅助方法 ===

    async def _http_get(self, path: str, **kwargs) -> Dict[str, Any]:
        """HTTP GET 请求"""
        import httpx

        url = f"{self.bridge_url}{path}"
        async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
            response = await client.get(url, **kwargs)
            response.raise_for_status()
            return response.json()

    async def _http_post(self, path: str, json_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """HTTP POST 请求"""
        import httpx

        url = f"{self.bridge_url}{path}"
        async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
            response = await client.post(url, json=json_data, **kwargs)
            response.raise_for_status()
            return response.json()

    async def _retry_with_backoff(self, coro, max_retries: Optional[int] = None):
        """
        带退避的重试

        Args:
            coro: 协程函数
            max_retries: 最大重试次数，None 使用 self.max_retries

        Returns:
            协程返回值
        """
        max_retries = max_retries or self.max_retries
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                result = await coro()
                self._record_success()
                return result
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # 指数退避
                    logger.warning(
                        f"{self.__class__.__name__}: Attempt {attempt + 1} failed, "
                        f"retrying in {wait_time}s: {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"{self.__class__.__name__}: All {max_retries + 1} attempts failed"
                    )

        self._record_failure()
        raise last_error

    # === 转换为 CameraAction 接口 ===

    @abstractmethod
    def to_camera_action(self, command: DeviceCommand) -> "CameraAction":
        """
        将设备命令转换为 algorithm_validation 的 CameraAction

        Args:
            command: 设备命令

        Returns:
            CameraAction 对象
        """
        pass

    @abstractmethod
    def from_camera_action(self, action: "CameraAction") -> DeviceCommand:
        """
        将 algorithm_validation 的 CameraAction 转换为设备命令

        Args:
            action: CameraAction 对象

        Returns:
            设备命令
        """
        pass


class MockAdapter(DeviceAdapter):
    """
    Mock 设备适配器

    用于测试和降级场景
    """

    async def connect(self) -> bool:
        """Mock 连接"""
        logger.info("MockAdapter: Simulating connection")
        await asyncio.sleep(0.1)
        self._is_connected = True
        self.device_id = "mock-device-001"
        return True

    async def disconnect(self) -> bool:
        """Mock 断开"""
        logger.info("MockAdapter: Simulating disconnection")
        self._is_connected = False
        return True

    async def get_capabilities(self, force_refresh: bool = False) -> DeviceCapabilities:
        """Mock 能力查询"""
        if self._capabilities and not force_refresh and self.enable_cache:
            return self._capabilities

        from protocols.capabilities import DeviceType

        self._capabilities = DeviceCapabilities(
            device_id=self.device_id or "mock-device-001",
            device_type=DeviceType.MOCK,
            firmware_version="1.0.0-mock",
            serial_number="MOCK123456",
            gesture_control=False,
            audio_control=False,
        )
        return self._capabilities

    async def execute_command(self, command: DeviceCommand) -> CommandResult:
        """Mock 命令执行"""
        logger.info(f"MockAdapter: Simulating command {command.action}")
        await asyncio.sleep(0.05)

        from protocols.commands import CommandStatus

        return CommandResult(
            command_id=command.command_id,
            status=CommandStatus.SUCCESS,
            result={"mock": True},
            execution_time_ms=50.0,
        )

    async def subscribe_events(self, callback):
        """Mock 事件订阅"""
        logger.info("MockAdapter: Event subscription not implemented")

    def to_camera_action(self, command: DeviceCommand):
        """Mock 转换"""
        raise NotImplementedError("MockAdapter does not convert to CameraAction")

    def from_camera_action(self, action):
        """Mock 转换"""
        raise NotImplementedError("MockAdapter does not convert from CameraAction")
