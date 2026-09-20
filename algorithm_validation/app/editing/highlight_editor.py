"""
高光剪辑模块
根据高光片段从原视频中提取片段
"""

import subprocess
from pathlib import Path
from typing import List, Tuple
from loguru import logger

from app.core.settings import settings


class HighlightEditor:
    """
    高光剪辑器
    使用 FFmpeg 从原视频中提取高光片段
    """

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        """
        Args:
            ffmpeg_path: FFmpeg 可执行文件路径
        """
        self.ffmpeg_path = ffmpeg_path
        logger.info(f"HighlightEditor initialized: ffmpeg={ffmpeg_path}")

    def extract_highlights(
        self,
        input_video: Path,
        segments: List[Tuple[int, int]],
        output_path: Path,
        fps: int = 30,
        codec: str = "libx264",
    ) -> bool:
        """
        提取高光片段并合并为一个视频

        Args:
            input_video: 输入视频路径
            segments: 高光片段列表 [(start_ms, end_ms), ...]
            output_path: 输出视频路径
            fps: 输出帧率
            codec: 视频编码器

        Returns:
            是否成功
        """
        if not segments:
            logger.warning("No highlight segments to extract")
            return False

        if not input_video.exists():
            logger.error(f"Input video not found: {input_video}")
            return False

        logger.info(
            f"Extracting {len(segments)} highlight segments from {input_video.name}"
        )

        # 如果只有一个片段，直接提取
        if len(segments) == 1:
            return self._extract_single_segment(
                input_video, segments[0], output_path, fps, codec
            )

        # 多个片段：先提取每个片段，再合并
        temp_dir = output_path.parent / "temp_segments"
        temp_dir.mkdir(parents=True, exist_ok=True)

        segment_files = []
        for i, (start_ms, end_ms) in enumerate(segments):
            segment_file = temp_dir / f"segment_{i:03d}.mp4"
            success = self._extract_single_segment(
                input_video, (start_ms, end_ms), segment_file, fps, codec
            )
            if success:
                segment_files.append(segment_file)

        if not segment_files:
            logger.error("No segments extracted successfully")
            return False

        # 合并片段
        success = self._concat_segments(segment_files, output_path, codec)

        # 清理临时文件
        for f in segment_files:
            f.unlink(missing_ok=True)
        temp_dir.rmdir()

        return success

    def _extract_single_segment(
        self,
        input_video: Path,
        segment: Tuple[int, int],
        output_path: Path,
        fps: int,
        codec: str,
    ) -> bool:
        """提取单个片段"""
        start_ms, end_ms = segment
        start_sec = start_ms / 1000.0
        duration_sec = (end_ms - start_ms) / 1000.0

        logger.info(
            f"Extracting segment: {start_sec:.2f}s - {start_sec + duration_sec:.2f}s"
        )

        cmd = [
            self.ffmpeg_path,
            "-y",  # 覆盖输出文件
            "-ss", str(start_sec),  # 起始时间
            "-t", str(duration_sec),  # 持续时间
            "-i", str(input_video),  # 输入文件
            "-c:v", codec,  # 视频编码器
            "-r", str(fps),  # 帧率
            "-preset", "fast",  # 编码速度
            "-crf", "23",  # 质量（18-28，越小质量越高）
            "-c:a", "aac",  # 音频编码器
            "-b:a", "128k",  # 音频比特率
            str(output_path),
        ]

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=300,  # 5分钟超时
                check=True,
            )
            logger.info(f"Segment extracted: {output_path.name}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg extraction failed: {e.stderr.decode()}")
            return False

        except subprocess.TimeoutExpired:
            logger.error("FFmpeg extraction timeout")
            return False

    def _concat_segments(
        self, segment_files: List[Path], output_path: Path, codec: str
    ) -> bool:
        """合并多个片段"""
        logger.info(f"Concatenating {len(segment_files)} segments")

        # 创建文件列表
        concat_file = output_path.parent / "concat_list.txt"
        with open(concat_file, "w", encoding="utf-8") as f:
            for seg_file in segment_files:
                # FFmpeg concat 格式
                f.write(f"file '{seg_file.absolute()}'\n")

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",  # 直接复制，不重新编码
            str(output_path),
        ]

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=300,
                check=True,
            )
            logger.info(f"Segments concatenated: {output_path.name}")
            concat_file.unlink()
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg concat failed: {e.stderr.decode()}")
            concat_file.unlink(missing_ok=True)
            return False

        except subprocess.TimeoutExpired:
            logger.error("FFmpeg concat timeout")
            concat_file.unlink(missing_ok=True)
            return False
