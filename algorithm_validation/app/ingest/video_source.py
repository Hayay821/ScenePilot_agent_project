"""
视频源抽象接口和文件视频源实现
支持实时和快速模式，输出单调递增时间戳的帧
"""

import cv2
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator, Optional
from loguru import logger

from app.core.schemas import FramePacket
from app.core.settings import settings


class VideoSource(ABC):
    """视频源抽象基类"""

    @abstractmethod
    def __iter__(self) -> Iterator[FramePacket]:
        """迭代返回视频帧"""
        pass

    @abstractmethod
    def release(self):
        """释放资源"""
        pass

    @abstractmethod
    def get_info(self) -> dict:
        """获取视频信息"""
        pass


class FileVideoSource(VideoSource):
    """
    文件视频源
    支持本地 MP4/AVI 等格式，按时间戳迭代帧
    """

    def __init__(
        self,
        video_path: str | Path,
        realtime: bool = False,
        sample_fps: Optional[int] = None,
        max_dimension: Optional[int] = None,
    ):
        """
        Args:
            video_path: 视频文件路径
            realtime: 是否模拟实时播放（True=按原始帧率延迟，False=快速读取）
            sample_fps: 采样帧率（None=使用配置默认值）
            max_dimension: 最大尺寸（None=使用配置默认值）
        """
        self.video_path = Path(video_path)
        if not self.video_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")

        self.realtime = realtime
        self.sample_fps = sample_fps or settings.video_sample_fps
        self.max_dimension = max_dimension or settings.video_max_dimension

        # 打开视频
        self.cap = cv2.VideoCapture(str(self.video_path))
        if not self.cap.isOpened():
            raise RuntimeError(f"无法打开视频文件: {video_path}")

        # 获取视频属性
        self.original_fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.duration_ms = int((self.frame_count / self.original_fps) * 1000)

        # 计算采样间隔
        self.sample_interval = int(self.original_fps / self.sample_fps)
        if self.sample_interval < 1:
            self.sample_interval = 1

        # 实时模式的延迟时间（毫秒）
        self.frame_delay_ms = int(1000 / self.sample_fps) if realtime else 0

        # 内部状态
        self._frame_index = 0
        self._last_read_time = None
        self._source_id = self.video_path.stem

        logger.info(
            f"VideoSource initialized: {self.video_path.name} "
            f"({self.width}x{self.height}, {self.original_fps:.1f}fps, "
            f"{self.frame_count} frames, {self.duration_ms}ms) "
            f"-> sample at {self.sample_fps}fps, realtime={realtime}"
        )

    def __iter__(self) -> Iterator[FramePacket]:
        """迭代返回采样后的视频帧"""
        self._frame_index = 0
        self._last_read_time = time.time() if self.realtime else None

        while True:
            # 读取下一帧
            ret, frame = self.cap.read()
            if not ret:
                logger.info(f"视频读取完毕: {self._frame_index} 帧")
                break

            current_frame_index = self._frame_index
            self._frame_index += 1

            # 采样：只处理间隔帧
            if current_frame_index % self.sample_interval != 0:
                continue

            # 计算时间戳（毫秒）
            timestamp_ms = int((current_frame_index / self.original_fps) * 1000)

            # 缩放帧
            resized_frame = self._resize_frame(frame)
            h, w = resized_frame.shape[:2]

            # 创建 FramePacket
            packet = FramePacket(
                source_id=self._source_id,
                frame_index=current_frame_index,
                timestamp_ms=timestamp_ms,
                image_path=None,  # 暂时不保存，由调用方决定
                width=w,
                height=h,
            )

            # 实时模式：模拟播放延迟
            if self.realtime and self._last_read_time is not None:
                elapsed = (time.time() - self._last_read_time) * 1000
                sleep_time = max(0, self.frame_delay_ms - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time / 1000)

            self._last_read_time = time.time() if self.realtime else None

            yield packet

    def _resize_frame(self, frame):
        """缩放帧到最大尺寸，保持宽高比"""
        h, w = frame.shape[:2]

        if max(h, w) <= self.max_dimension:
            return frame

        # 计算缩放比例
        if h > w:
            new_h = self.max_dimension
            new_w = int(w * (self.max_dimension / h))
        else:
            new_w = self.max_dimension
            new_h = int(h * (self.max_dimension / w))

        return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

    def release(self):
        """释放视频资源"""
        if self.cap is not None:
            self.cap.release()
            logger.info(f"VideoSource released: {self.video_path.name}")

    def get_info(self) -> dict:
        """获取视频信息"""
        return {
            "source_id": self._source_id,
            "path": str(self.video_path),
            "width": self.width,
            "height": self.height,
            "fps": self.original_fps,
            "frame_count": self.frame_count,
            "duration_ms": self.duration_ms,
            "sample_fps": self.sample_fps,
            "sample_interval": self.sample_interval,
            "realtime": self.realtime,
        }

    def __enter__(self):
        """上下文管理器"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """自动释放资源"""
        self.release()

    def __del__(self):
        """析构时确保资源释放"""
        self.release()
