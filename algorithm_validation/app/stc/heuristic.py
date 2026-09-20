"""
启发式 STC 实现
基于帧差、直方图、感知哈希等特征选择关键帧
"""

import cv2
import numpy as np
import imagehash
from PIL import Image
from typing import Optional
from loguru import logger

from app.core.schemas import FramePacket, SelectedFrame
from app.core.settings import settings
from .base import STCAdapter


class HeuristicSTC(STCAdapter):
    """
    启发式 STC 实现
    使用多种特征计算变化分数，选择关键帧
    """

    def __init__(
        self,
        frame_diff_threshold: Optional[float] = None,
        hist_diff_threshold: Optional[float] = None,
        phash_threshold: Optional[int] = None,
        max_gap_sec: Optional[int] = None,
        window_size_sec: Optional[int] = None,
        min_frames_per_window: Optional[int] = None,
        max_frames_per_window: Optional[int] = None,
    ):
        """
        Args:
            frame_diff_threshold: 灰度帧差阈值
            hist_diff_threshold: 直方图差异阈值
            phash_threshold: 感知哈希汉明距离阈值
            max_gap_sec: 最大帧间隔（秒）
            window_size_sec: 窗口大小（秒）
            min_frames_per_window: 每窗口最少帧数
            max_frames_per_window: 每窗口最多帧数
        """
        # 加载配置
        self.frame_diff_threshold = frame_diff_threshold or settings.stc_frame_diff_threshold
        self.hist_diff_threshold = hist_diff_threshold or settings.stc_hist_diff_threshold
        self.phash_threshold = phash_threshold or settings.stc_phash_threshold
        self.max_gap_sec = max_gap_sec or settings.stc_max_gap_sec
        self.max_gap_ms = self.max_gap_sec * 1000
        self.window_size_sec = window_size_sec or settings.stc_window_size_sec
        self.window_size_ms = self.window_size_sec * 1000
        self.min_frames_per_window = (
            min_frames_per_window or settings.stc_min_frames_per_window
        )
        self.max_frames_per_window = (
            max_frames_per_window or settings.stc_max_frames_per_window
        )

        # 内部状态
        self._last_frame_data = None
        self._last_frame_gray = None
        self._last_frame_hist = None
        self._last_frame_phash = None
        self._last_selected_timestamp = None
        self._current_window_start = 0
        self._current_window_frames = []

        # 统计
        self._total_frames = 0
        self._selected_frames = 0

        logger.info(
            f"HeuristicSTC initialized: "
            f"frame_diff={self.frame_diff_threshold}, "
            f"hist_diff={self.hist_diff_threshold}, "
            f"phash={self.phash_threshold}, "
            f"max_gap={self.max_gap_sec}s, "
            f"window={self.window_size_sec}s ({self.min_frames_per_window}-{self.max_frames_per_window} frames)"
        )

    def select(
        self,
        frame: FramePacket,
        frame_data: Optional[np.ndarray] = None,
        context: Optional[dict] = None,
    ) -> Optional[SelectedFrame]:
        """选择关键帧"""
        self._total_frames += 1

        # 检查窗口是否需要重置
        if frame.timestamp_ms >= self._current_window_start + self.window_size_ms:
            self._process_window_end()
            self._current_window_start = frame.timestamp_ms

        # 第一帧必选
        if self._last_frame_data is None:
            selected = self._create_selected_frame(
                frame, frame_data, 1.0, 1.0, ["first_frame"]
            )
            self._update_state(frame, frame_data)
            self._current_window_frames.append(selected)
            return selected

        # 计算各种变化分数
        frame_diff_score = self._compute_frame_diff(frame_data)
        hist_diff_score = self._compute_hist_diff(frame_data)
        phash_distance = self._compute_phash_distance(frame_data)

        # 综合变化分数（权重可调）
        change_score = (
            0.40 * frame_diff_score
            + 0.35 * hist_diff_score
            + 0.25 * (phash_distance / 64.0)  # 归一化到 0-1
        )

        # 判断是否选择
        selection_reasons = []
        should_select = False

        # 规则 1: 变化显著
        if frame_diff_score >= self.frame_diff_threshold:
            selection_reasons.append(f"high_frame_diff({frame_diff_score:.3f})")
            should_select = True

        if hist_diff_score >= self.hist_diff_threshold:
            selection_reasons.append(f"high_hist_diff({hist_diff_score:.3f})")
            should_select = True

        if phash_distance >= self.phash_threshold:
            selection_reasons.append(f"high_phash_dist({phash_distance})")
            should_select = True

        # 规则 2: 距离上次选择超过最大间隔
        if self._last_selected_timestamp is not None:
            gap_ms = frame.timestamp_ms - self._last_selected_timestamp
            if gap_ms >= self.max_gap_ms:
                selection_reasons.append(f"max_gap_exceeded({gap_ms}ms)")
                should_select = True

        # 规则 3: 窗口内帧数控制
        window_frame_count = len(self._current_window_frames)
        if window_frame_count < self.min_frames_per_window:
            # 还未达到最小帧数，降低阈值
            if change_score >= self.frame_diff_threshold * 0.7:
                selection_reasons.append("window_min_frames")
                should_select = True
        elif window_frame_count >= self.max_frames_per_window:
            # 已达最大帧数，提高阈值
            if should_select and change_score < self.frame_diff_threshold * 1.5:
                should_select = False
                selection_reasons.append("window_max_frames_skip")

        # 创建结果
        if should_select:
            selected = self._create_selected_frame(
                frame, frame_data, change_score, 0.5, selection_reasons
            )
            self._update_state(frame, frame_data)
            self._current_window_frames.append(selected)
            return selected
        else:
            # 更新参考帧（即使不选中，也作为下一帧的对比基准）
            self._update_state(frame, frame_data)
            return None

    def _compute_frame_diff(self, frame_data: np.ndarray) -> float:
        """计算灰度帧差"""
        if frame_data is None or self._last_frame_gray is None:
            return 0.0

        # 转灰度
        if len(frame_data.shape) == 3:
            gray = cv2.cvtColor(frame_data, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame_data

        # 计算绝对差的均值
        diff = cv2.absdiff(gray, self._last_frame_gray)
        mean_diff = np.mean(diff) / 255.0  # 归一化到 0-1

        return mean_diff

    def _compute_hist_diff(self, frame_data: np.ndarray) -> float:
        """计算 HSV 直方图距离"""
        if frame_data is None or self._last_frame_hist is None:
            return 0.0

        # 转 HSV
        if len(frame_data.shape) == 3:
            hsv = cv2.cvtColor(frame_data, cv2.COLOR_BGR2HSV)
        else:
            # 灰度图无法计算 HSV 直方图
            return 0.0

        # 计算直方图
        hist = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
        cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)

        # 比较直方图（Bhattacharyya 距离）
        distance = cv2.compareHist(hist, self._last_frame_hist, cv2.HISTCMP_BHATTACHARYYA)

        return distance

    def _compute_phash_distance(self, frame_data: np.ndarray) -> int:
        """计算感知哈希汉明距离"""
        if frame_data is None or self._last_frame_phash is None:
            return 0

        # 转 PIL Image
        if len(frame_data.shape) == 3:
            # BGR to RGB
            rgb = cv2.cvtColor(frame_data, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
        else:
            pil_img = Image.fromarray(frame_data)

        # 计算感知哈希
        phash = imagehash.phash(pil_img)

        # 汉明距离
        distance = phash - self._last_frame_phash

        return distance

    def _create_selected_frame(
        self,
        frame: FramePacket,
        frame_data: Optional[np.ndarray],
        change_score: float,
        novelty_score: float,
        selection_reasons: list[str],
    ) -> SelectedFrame:
        """创建 SelectedFrame 对象"""
        self._selected_frames += 1

        return SelectedFrame(
            frame=frame,
            change_score=min(change_score, 1.0),  # 确保不超过 1.0
            novelty_score=novelty_score,
            selection_reason=selection_reasons,
        )

    def _update_state(self, frame: FramePacket, frame_data: Optional[np.ndarray]):
        """更新内部状态"""
        if frame_data is None:
            return

        self._last_frame_data = frame_data
        self._last_selected_timestamp = frame.timestamp_ms

        # 更新灰度图
        if len(frame_data.shape) == 3:
            self._last_frame_gray = cv2.cvtColor(frame_data, cv2.COLOR_BGR2GRAY)
        else:
            self._last_frame_gray = frame_data

        # 更新直方图
        if len(frame_data.shape) == 3:
            hsv = cv2.cvtColor(frame_data, cv2.COLOR_BGR2HSV)
            hist = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
            cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
            self._last_frame_hist = hist

        # 更新感知哈希
        if len(frame_data.shape) == 3:
            rgb = cv2.cvtColor(frame_data, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
        else:
            pil_img = Image.fromarray(frame_data)
        self._last_frame_phash = imagehash.phash(pil_img)

    def _process_window_end(self):
        """处理窗口结束"""
        window_count = len(self._current_window_frames)
        logger.debug(
            f"Window closed: {window_count} frames selected "
            f"({self.min_frames_per_window}-{self.max_frames_per_window} target)"
        )
        self._current_window_frames = []

    def reset(self):
        """重置内部状态"""
        self._last_frame_data = None
        self._last_frame_gray = None
        self._last_frame_hist = None
        self._last_frame_phash = None
        self._last_selected_timestamp = None
        self._current_window_start = 0
        self._current_window_frames = []
        logger.info("HeuristicSTC reset")

    def get_stats(self) -> dict:
        """获取统计信息"""
        compression_ratio = 0.0
        if self._total_frames > 0:
            compression_ratio = 1.0 - (self._selected_frames / self._total_frames)

        return {
            "total_frames": self._total_frames,
            "selected_frames": self._selected_frames,
            "compression_ratio": compression_ratio,
            "config": {
                "frame_diff_threshold": self.frame_diff_threshold,
                "hist_diff_threshold": self.hist_diff_threshold,
                "phash_threshold": self.phash_threshold,
                "max_gap_sec": self.max_gap_sec,
                "window_size_sec": self.window_size_sec,
                "min_frames_per_window": self.min_frames_per_window,
                "max_frames_per_window": self.max_frames_per_window,
            },
        }
