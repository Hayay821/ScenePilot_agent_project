"""
端到端 CLI - 视频分析命令行接口
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Optional

import click
import cv2
from loguru import logger

from app.core.settings import settings
from app.core.schemas import SelectedFrame, RunMetrics
from app.ingest import FileVideoSource
from app.stc import HeuristicSTC
from app.semantic import MockSemanticProvider, DashScopeVLSemanticProvider
from app.director import DirectorStateMachine
from app.devices import MockDeviceAdapter
from app.editing import HighlightEditor


@click.group()
def cli():
    """ScenePilot - 事件驱动AI跟拍导演系统"""
    pass


@cli.command()
@click.option("--input", "-i", required=True, type=click.Path(exists=True), help="输入视频路径")
@click.option("--intent", required=True, type=str, help="用户意图描述")
@click.option("--output-dir", "-o", default="data/output", type=click.Path(), help="输出目录")
@click.option("--mock", is_flag=True, help="使用 Mock 模式（无需 API Key）")
@click.option("--realtime/--fast", default=False, help="实时模式/快速模式")
@click.option("--save-keyframes/--no-save-keyframes", default=True, help="是否保存关键帧")
def analyze(
    input: str,
    intent: str,
    output_dir: str,
    mock: bool,
    realtime: bool,
    save_keyframes: bool,
):
    """
    分析视频并生成导演决策

    示例:
        python -m app.cli analyze -i data/input/demo.mp4 --intent "跟拍骑马的人" --mock
    """
    asyncio.run(analyze_video(
        input_path=Path(input),
        user_intent=intent,
        output_dir=Path(output_dir),
        use_mock=mock,
        realtime=realtime,
        save_keyframes=save_keyframes,
    ))


async def analyze_video(
    input_path: Path,
    user_intent: str,
    output_dir: Path,
    use_mock: bool = False,
    realtime: bool = False,
    save_keyframes: bool = True,
):
    """视频分析主流程"""

    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    keyframes_dir = output_dir / "keyframes"
    keyframes_dir.mkdir(exist_ok=True)

    logger.info(f"=" * 60)
    logger.info(f"ScenePilot 视频分析")
    logger.info(f"=" * 60)
    logger.info(f"输入视频: {input_path}")
    logger.info(f"用户意图: {user_intent}")
    logger.info(f"输出目录: {output_dir}")
    logger.info(f"模式: {'Mock' if use_mock else 'Real API'}")
    logger.info(f"=" * 60)

    start_time = time.time()

    # 1. 初始化模块
    logger.info("📦 初始化模块...")

    stc = HeuristicSTC()

    if use_mock:
        semantic_provider = MockSemanticProvider()
    else:
        semantic_provider = DashScopeVLSemanticProvider()

    director = DirectorStateMachine()
    director_context = director.create_initial_context()

    device_adapter = MockDeviceAdapter(output_dir)

    # 2. 流式读取视频
    logger.info("🎥 开始流式读取视频...")

    selected_frames = []
    frame_count = 0

    with FileVideoSource(str(input_path), realtime=realtime) as source:
        # 打开视频读取器（用于获取帧图像）
        cap = cv2.VideoCapture(str(input_path))

        for frame_packet in source:
            frame_count += 1

            # 读取帧图像
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_packet.frame_index)
            ret, frame_data = cap.read()

            if not ret:
                logger.warning(f"Failed to read frame {frame_packet.frame_index}")
                continue

            # STC 选择
            selected = stc.select(frame_packet, frame_data)

            if selected is not None:
                # 保存关键帧图像
                if save_keyframes:
                    keyframe_path = keyframes_dir / f"frame_{frame_packet.frame_index:06d}.jpg"
                    cv2.imwrite(str(keyframe_path), frame_data)
                    selected.frame.image_path = str(keyframe_path)

                selected_frames.append(selected)

                logger.info(
                    f"  ✓ 选中第 {len(selected_frames)} 帧: "
                    f"index={frame_packet.frame_index}, "
                    f"time={frame_packet.timestamp_ms}ms, "
                    f"score={selected.change_score:.3f}"
                )

        cap.release()

    # STC 统计
    stc_stats = stc.get_stats()
    logger.info(f"🎯 STC 压缩完成:")
    logger.info(f"  总帧数: {stc_stats['total_frames']}")
    logger.info(f"  选中帧数: {stc_stats['selected_frames']}")
    logger.info(f"  压缩率: {stc_stats['compression_ratio']:.2%}")

    # 3. 语义分析
    logger.info("🧠 开始语义分析...")

    events = await semantic_provider.analyze(
        frames=selected_frames,
        user_intent=user_intent,
    )

    logger.info(f"✓ 检测到 {len(events)} 个事件:")
    for event in events:
        logger.info(
            f"  - {event.event_type}: {event.description[:50]} "
            f"({event.start_ms}-{event.end_ms}ms, score={event.highlight_score:.2f})"
        )

    # 保存事件
    events_file = output_dir / "events.jsonl"
    with open(events_file, "w", encoding="utf-8") as f:
        for event in events:
            f.write(event.model_dump_json() + "\n")
    logger.info(f"💾 事件已保存: {events_file}")

    # 4. 导演决策
    logger.info("🎬 生成导演决策...")

    # 获取当前时间戳（最后一帧的时间）
    current_timestamp = selected_frames[-1].frame.timestamp_ms if selected_frames else 0

    actions, director_context = director.process_events(
        events=events,
        context=director_context,
        current_timestamp_ms=current_timestamp,
    )

    logger.info(f"✓ 生成 {len(actions)} 条设备命令:")
    for action in actions:
        logger.info(f"  - {action.action_type} @ {action.timestamp_ms}ms")

    # 执行命令（Mock）
    device_adapter.execute_batch(actions)

    # 保存命令
    logger.info(f"💾 命令已保存: {output_dir / 'commands.jsonl'}")

    # 5. 高光剪辑
    logger.info("✂️  提取高光片段...")

    if director_context.highlight_segments:
        editor = HighlightEditor()
        highlight_output = output_dir / "highlights.mp4"

        success = editor.extract_highlights(
            input_video=input_path,
            segments=director_context.highlight_segments,
            output_path=highlight_output,
        )

        if success:
            logger.info(f"✓ 高光视频已生成: {highlight_output}")
        else:
            logger.error("✗ 高光视频生成失败")
    else:
        logger.warning("⚠️  未检测到高光片段")

    # 6. 生成运行指标
    end_time = time.time()
    elapsed_time = end_time - start_time

    metrics = RunMetrics(
        total_frames=stc_stats['total_frames'],
        selected_frames=stc_stats['selected_frames'],
        compression_ratio=stc_stats['compression_ratio'],
        events_detected=len(events),
        commands_generated=len(actions),
        highlight_segments=len(director_context.highlight_segments),
        processing_time_sec=elapsed_time,
        frames_per_second=stc_stats['total_frames'] / elapsed_time if elapsed_time > 0 else 0,
    )

    metrics_file = output_dir / "metrics.json"
    with open(metrics_file, "w", encoding="utf-8") as f:
        f.write(metrics.model_dump_json(indent=2))

    logger.info(f"=" * 60)
    logger.info(f"📊 运行指标:")
    logger.info(f"  处理时长: {elapsed_time:.2f}s")
    logger.info(f"  处理速度: {metrics.frames_per_second:.1f} fps")
    logger.info(f"  总帧数: {metrics.total_frames}")
    logger.info(f"  关键帧: {metrics.selected_frames}")
    logger.info(f"  压缩率: {metrics.compression_ratio:.2%}")
    logger.info(f"  事件数: {metrics.events_detected}")
    logger.info(f"  命令数: {metrics.commands_generated}")
    logger.info(f"  高光片段: {metrics.highlight_segments}")
    logger.info(f"=" * 60)
    logger.info(f"✅ 分析完成！输出目录: {output_dir}")
    logger.info(f"=" * 60)


@cli.command()
@click.option("--events", "-e", required=True, type=click.Path(exists=True), help="事件文件 (events.jsonl)")
def stats(events: str):
    """显示事件统计信息"""

    events_file = Path(events)

    logger.info(f"📊 事件统计: {events_file}")
    logger.info(f"=" * 60)

    # 读取事件
    from app.core.schemas import VideoEvent

    events_list = []
    with open(events_file, "r", encoding="utf-8") as f:
        for line in f:
            event_data = json.loads(line)
            events_list.append(VideoEvent(**event_data))

    # 统计
    event_types = {}
    total_duration = 0
    high_confidence = 0
    high_highlight = 0

    for event in events_list:
        # 事件类型
        event_types[event.event_type] = event_types.get(event.event_type, 0) + 1

        # 时长
        duration = event.end_ms - event.start_ms
        total_duration += duration

        # 置信度
        if event.confidence >= 0.8:
            high_confidence += 1

        # 高光
        if event.highlight_score >= 0.7:
            high_highlight += 1

    logger.info(f"总事件数: {len(events_list)}")
    logger.info(f"事件类型分布:")
    for event_type, count in sorted(event_types.items(), key=lambda x: -x[1]):
        logger.info(f"  - {event_type}: {count}")

    logger.info(f"总时长: {total_duration / 1000:.1f}s")
    logger.info(f"平均时长: {total_duration / len(events_list) / 1000:.1f}s")
    logger.info(f"高置信度事件: {high_confidence} ({high_confidence / len(events_list) * 100:.1f}%)")
    logger.info(f"高光事件: {high_highlight} ({high_highlight / len(events_list) * 100:.1f}%)")
    logger.info(f"=" * 60)


if __name__ == "__main__":
    cli()
