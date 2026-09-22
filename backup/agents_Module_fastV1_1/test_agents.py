"""独立测试各个 Agent 的脚本

每个 Agent 单独测试，输入单个文件，输出到独立子目录
"""
import argparse
import json
from pathlib import Path

from fast import (
    ScenePilotFast,
    MediaTools,
    OUTPUT_DIR,
    _json
)
from agents.skills_manager_agent import SkillsManagerAgent
from agents.director_agent import DirectorAgent
from agents.cinematographer_agent import CinematographerAgent
from agents.editor_agent import EditorAgent


def test_director(app: ScenePilotFast, text: str, image_path: str):
    """测试 Director Agent

    Args:
        app: ScenePilotFast 实例
        text: 用户拍摄目标
        image_path: 单张参考图片路径
    """
    print(f"\n{'='*60}")
    print("测试 Director Agent")
    print(f"{'='*60}")
    print(f"输入文本: {text}")
    print(f"参考图片: {image_path}")

    # 创建输出目录
    output_dir = OUTPUT_DIR / "director"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 获取相关 Skills
    selected_skills = app.skills.select(text, "director")
    if not selected_skills:
        selected_skills = [s for s in app.skills.list() if s.get("stage") == "director"][:1]

    print(f"匹配的 Skills: {[s['id'] for s in selected_skills]}")

    # 运行 Director
    result = app.director.run(text, selected_skills, [image_path])

    # 保存结果
    output_file = output_dir / "director.json"
    output_file.write_text(
        json.dumps(_json(result), ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"\n✅ Director 测试完成")
    print(f"输出目录: {output_dir}")
    print(f"结果文件: {output_file}")
    print(f"置信度: {result.get('confidence', 'N/A')}")
    if result.get('user_summary_zh'):
        print(f"总结: {result['user_summary_zh']}")

    return result


def test_cinematographer(app: ScenePilotFast, text: str, video_path: str):
    """测试 Cinematographer Agent

    Args:
        app: ScenePilotFast 实例
        text: 用户拍摄目标
        video_path: 单个视频文件路径
    """
    print(f"\n{'='*60}")
    print("测试 Cinematographer Agent")
    print(f"{'='*60}")
    print(f"输入文本: {text}")
    print(f"视频文件: {video_path}")

    # 创建输出目录
    output_dir = OUTPUT_DIR / "cinematographer"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 抽取视频帧
    video_name = Path(video_path).stem
    frames_dir = output_dir / "frames" / video_name
    print(f"\n正在抽取视频帧...")
    frames = MediaTools.extract_frames(video_path, frames_dir, every_seconds=2.0, max_frames=12)
    print(f"抽取了 {len(frames)} 帧")

    # 获取相关 Skills
    selected_skills = app.skills.select(text, "cinematographer")
    if not selected_skills:
        selected_skills = [s for s in app.skills.list() if s.get("stage") == "cinematographer"][:1]

    print(f"匹配的 Skills: {[s['id'] for s in selected_skills]}")

    # 运行 Cinematographer
    result = app.cinematographer.run(frames, selected_skills, text)

    # 保存结果
    output_file = output_dir / "filming.json"
    output_file.write_text(
        json.dumps(_json(result), ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"\n✅ Cinematographer 测试完成")
    print(f"输出目录: {output_dir}")
    print(f"结果文件: {output_file}")
    print(f"抽帧目录: {frames_dir}")
    if result.get('suggestion'):
        print(f"拍摄建议: {result['suggestion'].get('action', 'N/A')}")
    if result.get('captured_frame'):
        print(f"捕获帧: {result['captured_frame']}")
    if result.get('user_summary_zh'):
        print(f"总结: {result['user_summary_zh']}")

    return result


def test_editor(app: ScenePilotFast, video_path: str = None, image_path: str = None):
    """测试 Editor Agent

    Args:
        app: ScenePilotFast 实例
        video_path: 视频文件路径（可选）
        image_path: 图片文件路径（可选）
    """
    print(f"\n{'='*60}")
    print("测试 Editor Agent")
    print(f"{'='*60}")

    videos = [video_path] if video_path else []
    images = [image_path] if image_path else []

    print(f"视频素材: {videos}")
    print(f"图片素材: {images}")

    # 创建输出目录
    output_dir = OUTPUT_DIR / "editor"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 获取相关 Skills
    selected_skills = [s for s in app.skills.list() if s.get("stage") == "editor"][:1]
    if not selected_skills:
        selected_skills = app.skills.list()[:1]

    print(f"匹配的 Skills: {[s['id'] for s in selected_skills]}")

    # 运行 Editor
    result = app.editor.run(videos, images, selected_skills, output_dir)

    # 保存结果
    output_file = output_dir / "edit_plan.json"
    output_file.write_text(
        json.dumps(_json(result), ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"\n✅ Editor 测试完成")
    print(f"输出目录: {output_dir}")
    print(f"结果文件: {output_file}")
    if result.get('rendered_preview'):
        print(f"预览视频: {result['rendered_preview']}")
    if result.get('user_summary_zh'):
        print(f"总结: {result['user_summary_zh']}")

    return result


def test_skills_manager(app: ScenePilotFast, text: str, stage: str = "director"):
    """测试 SkillsManager Agent

    Args:
        app: ScenePilotFast 实例
        text: 用户输入的中文意图
        stage: 当前阶段（director/cinematographer/editor）
    """
    print(f"\n{'='*60}")
    print("测试 SkillsManager Agent")
    print(f"{'='*60}")
    print(f"输入文本: {text}")
    print(f"当前阶段: {stage}")

    # 创建输出目录
    output_dir = OUTPUT_DIR / "skills_manager"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 运行 SkillsManager
    result = app.manager.interact(text, stage)

    # 保存结果
    output_file = output_dir / f"skills_{stage}.json"
    output_file.write_text(
        json.dumps(_json(result), ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"\n✅ SkillsManager 测试完成")
    print(f"输出目录: {output_dir}")
    print(f"结果文件: {output_file}")
    print(f"匹配的 Skills: {[s['id'] for s in result.get('matched_skills', [])]}")
    if result.get('explanation_zh'):
        print(f"中文解释: {result['explanation_zh']}")

    return result


def main():
    parser = argparse.ArgumentParser(description="独立测试各个 Agent")
    parser.add_argument(
        "agent",
        choices=["skills", "director", "cinematographer", "editor", "all"],
        help="要测试的 Agent"
    )
    parser.add_argument("--mode", choices=["mock", "bailian"], default="bailian", help="运行模式")
    parser.add_argument("--text", default="请拍摄一组自然的人像短片", help="用户拍摄目标")
    parser.add_argument("--image", help="参考图片路径（用于 director）")
    parser.add_argument("--video", help="视频文件路径（用于 cinematographer 和 editor）")
    parser.add_argument("--stage", default="director", choices=["director", "cinematographer", "editor"], help="SkillsManager 的阶段")

    args = parser.parse_args()

    # 初始化应用
    print(f"\n初始化 ScenePilotFast (mode={args.mode})...")
    app = ScenePilotFast(mode=args.mode)

    # 运行测试
    if args.agent == "skills":
        test_skills_manager(app, args.text, args.stage)

    elif args.agent == "director":
        if not args.image:
            print("❌ 错误: Director 测试需要提供 --image 参数")
            return
        test_director(app, args.text, args.image)

    elif args.agent == "cinematographer":
        if not args.video:
            print("❌ 错误: Cinematographer 测试需要提供 --video 参数")
            return
        test_cinematographer(app, args.text, args.video)

    elif args.agent == "editor":
        if not args.video and not args.image:
            print("❌ 错误: Editor 测试需要提供 --video 或 --image 参数")
            return
        test_editor(app, args.video, args.image)

    elif args.agent == "all":
        # 测试所有 Agent
        print("\n" + "="*60)
        print("运行完整测试流程")
        print("="*60)

        # 1. SkillsManager
        test_skills_manager(app, args.text, "director")

        # 2. Director
        if args.image:
            test_director(app, args.text, args.image)
        else:
            print("\n⚠️  跳过 Director 测试（未提供 --image）")

        # 3. Cinematographer
        if args.video:
            test_cinematographer(app, args.text, args.video)
        else:
            print("\n⚠️  跳过 Cinematographer 测试（未提供 --video）")

        # 4. Editor
        if args.video or args.image:
            test_editor(app, args.video, args.image)
        else:
            print("\n⚠️  跳过 Editor 测试（未提供 --video 或 --image）")

        print(f"\n{'='*60}")
        print("所有测试完成")
        print(f"{'='*60}")
        print(f"输出根目录: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
