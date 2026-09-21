"""
Example: Complete workflow demonstration
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import agents_Module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents_Module.skills import SkillRepository, SkillValidator
from agents_Module.orchestration import AgentOrchestrator
from agents_Module.providers import MockProvider


def main():
    """Run complete agent workflow example"""

    print("=" * 60)
    print("ScenePilot Agent Module - Complete Workflow Demo")
    print("=" * 60)

    # 1. Initialize components
    print("\n[1/5] Initializing components...")

    base_path = Path(__file__).parent.parent / "skills" / "local_skills"
    base_path.mkdir(parents=True, exist_ok=True)

    repository = SkillRepository(str(base_path))
    validator = SkillValidator()
    provider = MockProvider()

    orchestrator = AgentOrchestrator(
        skill_repository=repository,
        skill_validator=validator,
        model_provider=provider,
        audit_log_path=str(base_path / "audit.jsonl")
    )

    print(f"✓ Repository initialized at: {base_path}")
    print(f"✓ Using MockProvider for deterministic testing")

    # 2. Run pre-production
    print("\n[2/5] Running pre-production workflow...")

    user_input = "我想拍摄一个动作挑战视频，记录完整的准备、动作和反应过程"

    pre_results = orchestrator.run_pre_production(
        user_input=user_input,
        available_devices=["link2", "x4air"],
        user_level="beginner"
    )

    # Display intent
    if "intent" in pre_results and pre_results["intent"].is_successful():
        intent = pre_results["intent"].output
        print(f"\n✓ Intent normalized:")
        print(f"  - Goal Type: {intent['goal']['goal_type']}")
        print(f"  - Style: {intent['goal'].get('style', 'N/A')}")
        print(f"  - Output: {intent['output']['ratio']} @ {intent['output']['duration_sec']}s")

    # Display retrieved skills
    if "skills" in pre_results and pre_results["skills"].is_successful():
        skills = pre_results["skills"].output["skills"]
        print(f"\n✓ Found {len(skills)} relevant skills:")
        for skill in skills:
            print(f"  - {skill['name']} (v{skill['version']})")

    # Display bundle
    if "bundle" in pre_results and pre_results["bundle"].is_successful():
        bundle = pre_results["bundle"].output
        print(f"\n✓ Skill bundle created with {len(bundle['skills'])} skills")

    # Display director plan
    if "plan" in pre_results and pre_results["plan"].is_successful():
        plan = pre_results["plan"].output
        print(f"\n✓ Director plan created:")
        print(f"  - Creative Goal: {plan['creative_goal']}")
        print(f"  - Priorities: {len(plan['priorities'])} items")
        print(f"  - Shot Intentions: {len(plan['shot_intentions'])} stages")

        for intention in plan['shot_intentions']:
            print(f"    • {intention['stage']}: {intention['camera']} - {intention['notes']}")

        if plan.get('teaching_notes'):
            print(f"\n  Teaching Notes:")
            for note in plan['teaching_notes']:
                print(f"    📝 {note}")

    # 3. Simulate filming step
    print("\n[3/5] Simulating filming recommendations...")

    # Check if plan was created successfully
    if "plan" not in pre_results or not pre_results["plan"].is_successful():
        print("⚠️  Skipping filming and post-production - no plan available")
        return 1

    # Mock subject at 5 seconds
    subject = {
        "id": "person_1",
        "type": "person",
        "bbox": [0.30, 0.20, 0.25, 0.65],
        "confidence": 0.92,
        "motion_vector": [0.1, 0.0],
        "pose": "standing"
    }

    rec_result = orchestrator.run_filming_step(
        subject=subject,
        timestamp_ms=5000,
        current_stage="main"
    )

    if rec_result.is_successful():
        rec = rec_result.output
        print(f"\n✓ Cinematographer recommendation @ 5.0s:")
        print(f"  - State: {rec['state']}")
        print(f"  - Composition: {rec['shot_strategy']['composition']}")
        print(f"  - Camera: {rec['shot_strategy']['camera_preference']}")
        print(f"  - Explanation: {rec['explanation']}")

        if rec['suggested_actions']:
            print(f"\n  Suggested Actions:")
            for action in rec['suggested_actions']:
                print(f"    → {action['device']}.{action['action']}: {action['reason']}")

    # 4. Run post-production
    print("\n[4/5] Running post-production workflow...")

    # Mock detected events
    events = [
        {
            "event_id": "evt_001",
            "event_type": "action_start",
            "start_ms": 1000,
            "end_ms": 2000,
            "confidence": 0.88,
            "subject_id": "person_1",
            "metadata": {}
        },
        {
            "event_id": "evt_002",
            "event_type": "action_peak",
            "start_ms": 3000,
            "end_ms": 5000,
            "confidence": 0.95,
            "subject_id": "person_1",
            "metadata": {}
        },
        {
            "event_id": "evt_003",
            "event_type": "celebration",
            "start_ms": 6000,
            "end_ms": 8000,
            "confidence": 0.80,
            "subject_id": "person_1",
            "metadata": {}
        }
    ]

    # Mock media sources
    media_sources = [
        {"source_id": "x4air_001", "duration_ms": 10000},
        {"source_id": "link2_001", "duration_ms": 12000},
        {"source_id": "x4air_002", "duration_ms": 8000}
    ]

    edit_result = orchestrator.run_post_production(
        events=events,
        media_sources=media_sources
    )

    if edit_result.is_successful():
        edit_plan = edit_result.output
        print(f"\n✓ Edit plan created:")
        print(f"  - Total Duration: {edit_plan['total_duration_ms'] / 1000:.1f}s")
        print(f"  - Segments: {len(edit_plan['timeline'])}")
        print(f"  - Render: {edit_plan['render']['ratio']} @ {edit_plan['render']['quality']}")

        print(f"\n  Timeline:")
        for i, segment in enumerate(edit_plan['timeline'], 1):
            duration = (segment['end_ms'] - segment['start_ms']) / 1000
            print(f"    {i}. [{segment['start_ms']/1000:.1f}s - {segment['end_ms']/1000:.1f}s] "
                  f"{segment['source_id']} ({duration:.1f}s) - {segment['role']}")

        if edit_plan.get('explanations'):
            print(f"\n  Explanations:")
            for exp in edit_plan['explanations']:
                print(f"    💡 {exp}")

    # 5. Session summary
    print("\n[5/5] Session summary...")

    summary = orchestrator.get_session_summary()
    print(f"\n✓ Workflow completed:")
    print(f"  - Session ID: {summary['session_id']}")
    print(f"  - Total Results: {summary['results_count']}")
    print(f"  - Has Intent: {summary['has_intent']}")
    print(f"  - Has Plan: {summary['has_plan']}")
    print(f"  - Audit Log: {orchestrator.audit_log_path}")

    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
