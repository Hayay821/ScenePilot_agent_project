"""
Example: Using DashScope API with Real Skills

Demonstrates how to integrate Alibaba Cloud DashScope (百炼) API
with the agent system for real model inference.
"""

import sys
from pathlib import Path
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents_Module.skills import SkillRepository, SkillValidator
from agents_Module.orchestration import AgentOrchestrator


def main():
    """Run workflow with DashScope API"""

    print("=" * 70)
    print("ScenePilot Agent Module - DashScope API Integration")
    print("=" * 70)
    print()

    # Check if DashScope is available
    try:
        from agents_Module.providers import DashScopeProvider, DASHSCOPE_AVAILABLE

        if not DASHSCOPE_AVAILABLE:
            print("❌ DashScope package not installed")
            print("\nInstall with:")
            print("  pip install dashscope")
            return

    except ImportError:
        print("❌ DashScope provider not available")
        print("\nInstall with:")
        print("  pip install dashscope")
        return

    # Check for API key
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("❌ DASHSCOPE_API_KEY environment variable not set")
        print("\nSet your API key:")
        print("  Windows CMD:  set DASHSCOPE_API_KEY=your-api-key-here")
        print("  PowerShell:   $env:DASHSCOPE_API_KEY='your-api-key-here'")
        print("  Linux/Mac:    export DASHSCOPE_API_KEY='your-api-key-here'")
        return

    print("✓ DashScope API configured")
    print()

    # Initialize provider
    try:
        provider = DashScopeProvider(
            api_key=api_key,
            model_name="qwen-max",  # or qwen-plus, qwen-turbo
            timeout=30,
            max_retries=3
        )
        print(f"✓ Using model: qwen-max")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize provider: {e}")
        return

    # Initialize skill repository
    repo_path = Path(__file__).parent.parent / "skills" / "repository"
    repo = SkillRepository(str(repo_path))
    validator = SkillValidator()

    print(f"✓ Skill repository: {repo_path}")
    print()

    # Initialize orchestrator with DashScope provider
    orchestrator = AgentOrchestrator(
        skill_repository=repo,
        skill_validator=validator,
        model_provider=provider
    )

    # Test cases
    test_cases = [
        {
            "name": "自然个人肖像",
            "user_input": "拍摄自然个人肖像用作社交媒体头像",
            "devices": ["osmo_pocket_3"],
            "user_level": "intermediate"
        },
        {
            "name": "夕阳人像剪影",
            "user_input": "在夕阳下拍摄人像剪影效果",
            "devices": ["osmo_pocket_3"],
            "user_level": "beginner"
        },
        {
            "name": "创意双人互动",
            "user_input": "拍摄双人创意互动的有趣瞬间",
            "devices": ["osmo_pocket_3"],
            "user_level": "advanced"
        }
    ]

    # Run test case
    for i, test in enumerate(test_cases, 1):
        print("=" * 70)
        print(f"Test Case {i}: {test['name']}")
        print("=" * 70)
        print()

        try:
            # Run complete workflow
            result = orchestrator.run_complete_workflow(
                user_input=test["user_input"],
                devices=test["devices"],
                user_level=test["user_level"]
            )

            # Display results
            print(f"✓ Session: {result['session_id']}")
            print()

            # Director plan
            if "director_plan" in result:
                plan = result["director_plan"]
                print("📋 Director Plan:")
                print(f"  Goal: {plan['creative_goal']}")
                print(f"  Priorities: {', '.join(plan['priorities'][:3])}")
                print(f"  Shot Intentions: {len(plan['shot_intentions'])} phases")
                print()

            # Editor timeline
            if "edit_plan" in result:
                edit = result["edit_plan"]
                print("🎬 Edit Plan:")
                print(f"  Segments: {len(edit['timeline'])}")
                print(f"  Total Duration: {edit['total_duration_ms'] / 1000:.1f}s")
                print()

            # Teaching notes
            if "teaching_notes" in result:
                notes = result["teaching_notes"]
                if notes:
                    print("💡 Teaching Notes:")
                    for note in notes[:3]:  # Show first 3
                        print(f"  • {note}")
                    print()

            print(f"✓ Workflow completed successfully!")
            print()

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            print()

        # Only run first test case to save API calls
        print("Note: Running only first test case to save API calls")
        print("      Remove this break to run all test cases")
        break

    print("=" * 70)
    print("Demo Complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
