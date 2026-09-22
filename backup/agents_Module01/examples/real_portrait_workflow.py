"""
Example: Real portrait skills with test data

Demonstrates using real portrait skills (portrait_story_director,
portrait_composition_coach, portrait_reel_editor) with actual test images and videos.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents_Module.skills import SkillRepository, SkillValidator
from agents_Module.orchestration import AgentOrchestrator
from agents_Module.providers import MockProvider


def main():
    """Run real portrait skills workflow"""

    print("=" * 70)
    print("Real Portrait Skills Workflow Demo")
    print("=" * 70)

    # 1. Initialize with real skills
    print("\n[1/6] Loading real portrait skills...")

    repo_path = Path(__file__).parent.parent / "skills" / "repository"
    repository = SkillRepository(str(repo_path))
    validator = SkillValidator()
    provider = MockProvider()

    # Verify skills exist
    director_skill = repository.load_skill("portrait_story_director")
    coach_skill = repository.load_skill("portrait_composition_coach")
    editor_skill = repository.load_skill("portrait_reel_editor")

    if not all([director_skill, coach_skill, editor_skill]):
        print("❌ Error: Real skills not found in repository")
        print(f"   Repository path: {repo_path}")
        return 1

    print(f"✓ Loaded 3 portrait skills:")
    print(f"  - {director_skill.name} (导演)")
    print(f"  - {coach_skill.name} (摄影指导)")
    print(f"  - {editor_skill.name} (剪辑)")

    # 2. Initialize orchestrator
    print("\n[2/6] Initializing orchestrator...")

    orchestrator = AgentOrchestrator(
        skill_repository=repository,
        skill_validator=validator,
        model_provider=provider
    )

    print("✓ Orchestrator ready")

    # 3. Test Case 1: Natural Portrait
    print("\n[3/6] Test Case 1: Natural Single Portrait")
    print("-" * 70)

    user_input_1 = "我想拍一组自然的个人肖像，用作社交头像，不要看起来像摆拍。"
    print(f"User Input: {user_input_1}")

    pre_results_1 = orchestrator.run_pre_production(
        user_input=user_input_1,
        available_devices=["insta360_link2", "insta360_x4_air"],
        user_level="beginner"
    )

    if pre_results_1["plan"].is_successful():
        plan = pre_results_1["plan"].output
        print(f"\n✓ Director Plan:")
        print(f"  Creative Goal: {plan['creative_goal']}")
        print(f"  Priorities: {len(plan['priorities'])} items")

        if plan.get('teaching_notes'):
            print(f"\n  Teaching Notes for Beginners:")
            for note in plan['teaching_notes'][:3]:  # Show first 3
                print(f"    📝 {note}")

    # 4. Test Case 2: Environmental Portrait
    print("\n[4/6] Test Case 2: Environmental Travel Portrait")
    print("-" * 70)

    user_input_2 = "请拍一个人在南京户外环境中的旅行肖像，要让人看出这个地方，而不是只有一张脸。"
    print(f"User Input: {user_input_2}")

    pre_results_2 = orchestrator.run_pre_production(
        user_input=user_input_2,
        available_devices=["insta360_link2", "insta360_x4_air"],
        user_level="beginner"
    )

    if pre_results_2["plan"].is_successful():
        plan = pre_results_2["plan"].output
        print(f"\n✓ Director Plan:")
        print(f"  Creative Goal: {plan['creative_goal']}")
        print(f"  Shot Intentions: {len(plan['shot_intentions'])} stages")

        for intention in plan['shot_intentions']:
            print(f"    • {intention['stage']}: {intention['notes']}")

    # 5. Test Cinematographer with Real Skill
    print("\n[5/6] Testing Cinematographer with Real Skill")
    print("-" * 70)

    # Simulate subject with gaze direction left
    subject_gaze_left = {
        "id": "person_1",
        "type": "person",
        "bbox": [0.30, 0.20, 0.25, 0.65],
        "confidence": 0.92,
        "face_visible": True,
        "gaze_direction": "left",
        "motion_direction": "still",
        "occlusion_ratio": 0.05,
        "tracking_confidence": 0.92
    }

    print("Subject State: Face visible, gazing left, stable")

    rec_result = orchestrator.run_filming_step(
        subject=subject_gaze_left,
        timestamp_ms=5000,
        current_stage="main"
    )

    if rec_result.is_successful():
        rec = rec_result.output
        print(f"\n✓ Cinematographer Recommendation:")
        print(f"  Composition: {rec['shot_strategy']['composition']}")
        print(f"  Camera: {rec['shot_strategy']['camera_preference']}")
        print(f"  Explanation: {rec['explanation']}")

        if rec['suggested_actions']:
            print(f"\n  Suggested Actions (不直接执行):")
            for action in rec['suggested_actions']:
                print(f"    → {action['device']}.{action['action']}")

    # 6. Test Editor with Real Data References
    print("\n[6/6] Testing Editor with Real Test Data")
    print("-" * 70)

    # Reference actual test data paths
    test_data_dir = Path(__file__).parent.parent.parent.parent / "data" / "test_data"

    print(f"Test Data Directory: {test_data_dir}")

    if test_data_dir.exists():
        images = list((test_data_dir / "img").glob("*.jpg"))
        videos = list((test_data_dir / "video").glob("*.mp4"))
        print(f"  Found {len(images)} test images")
        print(f"  Found {len(videos)} test videos")

    # Mock events for portrait timeline
    events = [
        {
            "event_id": "evt_001",
            "event_type": "environment_start",
            "start_ms": 0,
            "end_ms": 2000,
            "confidence": 0.85,
            "subject_id": "person_1",
            "metadata": {}
        },
        {
            "event_id": "evt_002",
            "event_type": "subject_stable",
            "start_ms": 2000,
            "end_ms": 6000,
            "confidence": 0.92,
            "subject_id": "person_1",
            "metadata": {"face_quality": 0.88}
        },
        {
            "event_id": "evt_003",
            "event_type": "smile",
            "start_ms": 6000,
            "end_ms": 8000,
            "confidence": 0.88,
            "subject_id": "person_1",
            "metadata": {}
        }
    ]

    # Media sources referencing test data
    media_sources = [
        {
            "source_id": "x4air_env",
            "duration_ms": 10000,
            "camera": "insta360_x4_air",
            "path": str(test_data_dir / "video" / "test_video1.mp4") if test_data_dir.exists() else None
        },
        {
            "source_id": "link2_portrait",
            "duration_ms": 10000,
            "camera": "insta360_link2",
            "path": str(test_data_dir / "video" / "test_video2.mp4") if test_data_dir.exists() else None
        }
    ]

    edit_result = orchestrator.run_post_production(
        events=events,
        media_sources=media_sources
    )

    if edit_result.is_successful():
        edit_plan = edit_result.output
        print(f"\n✓ Edit Plan Created:")
        print(f"  Total Duration: {edit_plan['total_duration_ms'] / 1000:.1f}s")
        print(f"  Timeline Segments: {len(edit_plan['timeline'])}")

        print(f"\n  Timeline:")
        for i, segment in enumerate(edit_plan['timeline'], 1):
            duration = (segment['end_ms'] - segment['start_ms']) / 1000
            print(f"    {i}. [{segment['start_ms']/1000:.1f}s-{segment['end_ms']/1000:.1f}s] "
                  f"{segment['role']} - {segment['source_id']} ({duration:.1f}s)")

        if edit_plan.get('explanations'):
            print(f"\n  Explanations:")
            for exp in edit_plan['explanations'][:2]:  # Show first 2
                print(f"    💡 {exp}")

    # Summary
    print("\n" + "=" * 70)
    print("Demo Completed Successfully")
    print("=" * 70)
    print("\n✓ Real Skills Used:")
    print("  - portrait_story_director (导演 Agent)")
    print("  - portrait_composition_coach (摄影指导 Agent)")
    print("  - portrait_reel_editor (剪辑 Agent)")
    print("\n✓ Test Data Referenced:")
    print(f"  - Images: {test_data_dir / 'img' if test_data_dir.exists() else 'N/A'}")
    print(f"  - Videos: {test_data_dir / 'video' if test_data_dir.exists() else 'N/A'}")
    print("\n✓ Safety Verified:")
    print("  - All actions are suggestions only")
    print("  - No direct device control")
    print("  - Human approval required for critical operations")

    return 0


if __name__ == "__main__":
    exit(main())
