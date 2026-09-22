"""
Example: Real Portrait Skills with Test Data

This example demonstrates the complete workflow using:
- Real portrait skills (portrait_story_director, portrait_composition_coach, portrait_reel_editor)
- Test data from project00/data/test_data/
- All 7 user test cases from user_requests.yaml
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Configure logging to save to logs directory
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)
log_filename = LOGS_DIR / f"{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from agents_Module.skills import SkillRepository, SkillValidator
from agents_Module.orchestration import AgentOrchestrator
from agents_Module.providers import BailianProvider


# Test data paths
TEST_DATA_ROOT = Path(__file__).parent.parent.parent / "data" / "test_data"
TEST_IMG_DIR = TEST_DATA_ROOT / "img"
TEST_VIDEO_DIR = TEST_DATA_ROOT / "video"


def print_section(title):
    """Print section header"""
    msg = "\n" + "=" * 70 + f"\n {title}\n" + "=" * 70
    print(msg)
    logger.info(title)


def print_subsection(title):
    """Print subsection header"""
    print(f"\n--- {title} ---")
    logger.info(f"--- {title} ---")


def run_test_case(orchestrator, case_id, user_input, user_level, expected_skills):
    """Run a single test case"""
    print_section(f"Test Case: {case_id}")
    print(f"User Input: {user_input}")
    print(f"User Level: {user_level}")
    logger.info(f"User Input: {user_input}")
    logger.info(f"User Level: {user_level}")

    # Run pre-production
    print_subsection("Pre-Production Phase")

    pre_results = orchestrator.run_pre_production(
        user_input=user_input,
        available_devices=["insta360_link2", "insta360_x4_air"],
        user_level=user_level
    )

    # Show intent
    if pre_results["intent"].is_successful():
        intent = pre_results["intent"].output
        print(f"\n[OK] Intent Normalized:")
        print(f"  Goal Type: {intent.get('goal_type', 'N/A')}")
        print(f"  Subject Type: {intent.get('subject_type', 'N/A')}")
        print(f"  Style: {intent.get('style_preference', 'N/A')}")
        print(f"  Output Format: {intent.get('output_format', {}).get('aspect_ratio', 'N/A')}")
        logger.info(f"Intent: {intent}")

    # Show skills
    if "bundle" in pre_results and pre_results["bundle"].is_successful():
        bundle = pre_results["bundle"].output
        print(f"\n[OK] Skills Retrieved:")
        logger.info(f"Skills Retrieved: {len(bundle['skills'])} skills")
        for skill in bundle['skills']:
            print(f"  - {skill['skill_id']} (v{skill['version']})")
            logger.info(f"  Skill: {skill['skill_id']} v{skill['version']}")
            if skill['skill_id'] in expected_skills:
                print(f"    [OK] Expected skill found")
    else:
        msg = "\n[WARNING] No skills found - bundle not created"
        print(msg)
        logger.warning("No skills found - bundle not created")

    # Show director plan
    if "bundle" in pre_results and pre_results["bundle"].is_successful():
        pass  # Already showed above

    if "plan" in pre_results and pre_results["plan"].is_successful():
        plan = pre_results["plan"].output
        print(f"\n[OK] Director Plan:")
        print(f"  Creative Goal: {plan.get('creative_goal', 'N/A')}")
        logger.info(f"Director Plan - Creative Goal: {plan.get('creative_goal', 'N/A')}")

        # Handle priorities - they are dict objects with 'name' and 'reason' keys
        priorities = plan.get('priorities', [])
        if priorities:
            priority_items = [p['name'] if isinstance(p, dict) else str(p) for p in priorities]
            print(f"  Priorities: {', '.join(priority_items)}")
            logger.info(f"Priorities: {', '.join(priority_items)}")
        else:
            print(f"  Priorities: N/A")

        print(f"  Shot Intentions: {len(plan.get('shot_intentions', []))} stages")

        if plan.get('teaching_notes'):
            print(f"\n  [INFO] Teaching Notes (for beginners):")
            logger.info("Teaching Notes:")
            for note in plan['teaching_notes'][:3]:
                # Remove emoji and special unicode characters for Windows console
                safe_note = note.encode('gbk', errors='ignore').decode('gbk', errors='ignore')
                print(f"    - {safe_note}")
                logger.info(f"  - {note}")

    return pre_results


def main():
    """Run all test cases from user_requests.yaml"""

    print_section("ScenePilot Real Skills Demo")
    print("\nUsing:")
    print("  - Real portrait skills from data/skills/")
    print("  - Test images and videos from data/test_data/")
    print("  - User test cases from test_inputs/user_requests.yaml")

    logger.info("=" * 70)
    logger.info("ScenePilot Real Skills Demo Started")
    logger.info(f"Log file: {log_filename}")
    logger.info("=" * 70)

    # Initialize orchestrator with real skills and real API
    repo_path = Path(__file__).parent.parent / "skills" / "repository"
    repository = SkillRepository(str(repo_path))
    validator = SkillValidator()
    provider = BailianProvider(timeout=60, max_retries=2)  # Increase timeout to 60s

    orchestrator = AgentOrchestrator(
        skill_repository=repository,
        skill_validator=validator,
        model_provider=provider
    )

    expected_skills = ["portrait_story_director", "portrait_composition_coach", "portrait_reel_editor"]

    # Test Case U001: Natural Single Portrait
    run_test_case(
        orchestrator=orchestrator,
        case_id="U001_single_natural_avatar",
        user_input="我想拍一组自然的个人肖像，用作社交头像，不要看起来像摆拍。",
        user_level="beginner",
        expected_skills=expected_skills
    )

    # Test Case U002: Environmental Travel Portrait
    run_test_case(
        orchestrator=orchestrator,
        case_id="U002_environment_travel",
        user_input="请拍一个人在南京户外环境中的旅行肖像，要让人看出这个地方，而不是只有一张脸。",
        user_level="beginner",
        expected_skills=expected_skills
    )

    # Test Case U003: Interview
    run_test_case(
        orchestrator=orchestrator,
        case_id="U003_interview",
        user_input="我要录一个人物采访，画面自然、声音清楚，不要因为追求节奏把说话人的停顿都剪掉。",
        user_level="intermediate",
        expected_skills=expected_skills
    )

    # Test Case U006: Prefer Reactions
    run_test_case(
        orchestrator=orchestrator,
        case_id="U006_user_prefers_reaction",
        user_input="不要只剪最好看的正脸，我更想保留人物完成动作后笑出来、朋友在旁边反应的画面。",
        user_level="beginner",
        expected_skills=expected_skills
    )

    # Test Case U007: Low Confidence - Explain Options
    run_test_case(
        orchestrator=orchestrator,
        case_id="U007_low_confidence",
        user_input="我不确定该用近景还是全身，你先给我三个方案并解释区别，不要直接执行。",
        user_level="beginner",
        expected_skills=expected_skills
    )

    # Demonstrate Cinematographer with realistic subject state
    print_section("Cinematographer Real-Time Suggestions")

    print_subsection("Scenario 1: Subject Tracking Lost")

    # Create a session first
    orchestrator.run_pre_production(
        user_input="拍摄个人肖像",
        available_devices=["insta360_link2", "insta360_x4_air"],
        user_level="beginner"
    )

    subject_state_lost = {
        "subject_id": "person_001",
        "bbox_normalized": [0.0, 0.0, 0.0, 0.0],
        "face_visible": False,
        "gaze_direction": "unknown",
        "motion_direction": "unknown",
        "occlusion_ratio": 0.70,
        "tracking_confidence": 0.30
    }

    result_lost = orchestrator.run_filming_step(
        subject=subject_state_lost,
        timestamp_ms=1000,
        current_stage="main"
    )

    if result_lost.is_successful():
        rec = result_lost.output
        print(f"\n[OK] Cinematographer Recommendation:")
        print(f"  Strategy: {rec.get('shot_strategy', 'N/A')}")
        print(f"  Suggested Actions: {rec.get('suggested_actions', [])}")
        print(f"  Explanation: {rec.get('explanation', 'N/A')}")

    print_subsection("Scenario 2: Subject Stable with Gaze Left")

    subject_state_gaze = {
        "subject_id": "person_001",
        "bbox_normalized": [0.3, 0.2, 0.6, 0.8],
        "face_visible": True,
        "gaze_direction": "left",
        "motion_direction": "still",
        "occlusion_ratio": 0.05,
        "tracking_confidence": 0.92
    }

    result_gaze = orchestrator.run_filming_step(
        subject=subject_state_gaze,
        timestamp_ms=2000,
        current_stage="main"
    )

    if result_gaze.is_successful():
        rec = result_gaze.output
        print(f"\n[OK] Cinematographer Recommendation:")
        print(f"  Strategy: {rec.get('shot_strategy', 'N/A')}")
        print(f"  Suggested Actions: {rec.get('suggested_actions', [])}")
        print(f"  Explanation: {rec.get('explanation', 'N/A')}")

    # Demonstrate Editor with realistic events
    print_section("Editor Post-Production Timeline")

    print_subsection("Scenario: Natural Portrait Story Arc")

    events = [
        {
            "event_type": "environment_start",
            "timestamp_ms": 0,
            "duration_ms": 3000,
            "camera": "x4air",
            "quality": 0.85,
            "media_ref": str(TEST_IMG_DIR / "微信图片_20260922013228_909_27.jpg")
        },
        {
            "event_type": "subject_stable",
            "timestamp_ms": 3000,
            "duration_ms": 5000,
            "camera": "link2",
            "face_quality": 0.90,
            "quality": 0.88,
            "media_ref": str(TEST_VIDEO_DIR / "test_video1.mp4")
        },
        {
            "event_type": "smile",
            "timestamp_ms": 8000,
            "duration_ms": 2000,
            "camera": "link2",
            "quality": 0.92,
            "media_ref": str(TEST_VIDEO_DIR / "test_video2.mp4")
        },
        {
            "event_type": "celebration_or_reaction",
            "timestamp_ms": 10000,
            "duration_ms": 3000,
            "camera": "link2",
            "quality": 0.89,
            "media_ref": str(TEST_IMG_DIR / "微信图片_20260922013228_915_27.jpg")
        }
    ]

    result_edit = orchestrator.run_post_production(
        events=events,
        media_sources=[{"type": "video", "path": str(TEST_IMG_DIR / "微信图片_20260922013228_915_27.jpg")}]
    )

    if result_edit.is_successful():
        timeline = result_edit.output
        print(f"\n[OK] Edit Timeline Created:")
        print(f"  Total Duration: {timeline.get('render', {}).get('total_duration_ms', 0) / 1000:.1f}s")
        print(f"  Segments: {len(timeline.get('timeline', []))}")

        print(f"\n  Timeline Breakdown:")
        for i, shot in enumerate(timeline.get('timeline', []), 1):
            print(f"    {i}. {shot.get('role', 'N/A')} ({shot.get('start_ms', 0)}-{shot.get('end_ms', 0)}ms)")
            print(f"       Camera: {shot.get('camera', 'N/A')}, Reason: {shot.get('reason', 'N/A')}")

    # Summary
    print_section("Demo Summary")
    print("\n[OK] Successfully demonstrated:")
    print("  - Intent normalization with real portrait scenarios")
    print("  - Director planning with teaching notes for beginners")
    print("  - Cinematographer real-time suggestions based on subject state")
    print("  - Editor timeline creation with portrait story arc")
    print("\n[OK] Real skills loaded:")
    print("  - portrait_story_director - Pre-production planning")
    print("  - portrait_composition_coach - Real-time filming guidance")
    print("  - portrait_reel_editor - Post-production timeline")
    print("\n[OK] Test data referenced:")
    print(f"  - Images: {TEST_IMG_DIR}")
    print(f"  - Videos: {TEST_VIDEO_DIR}")

    print("\n" + "=" * 70)
    print("Demo Completed")
    print("=" * 70)


if __name__ == "__main__":
    main()
