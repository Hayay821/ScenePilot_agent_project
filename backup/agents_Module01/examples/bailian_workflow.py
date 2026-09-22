"""
Example: Using Bailian (百炼) Provider for Real LLM Inference

This example shows how to use real Bailian API instead of MockProvider.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents_Module.skills import SkillRepository, SkillValidator
from agents_Module.orchestration import AgentOrchestrator
from agents_Module.providers import BailianProvider, create_from_config


def main():
    """Run workflow with real Bailian API"""

    print("=" * 70)
    print("ScenePilot Agent Module - Bailian API Demo")
    print("=" * 70)

    # 1. Initialize Bailian Provider
    print("\n[1/4] Initializing Bailian Provider...")

    # Method 1: From config file
    config_path = Path(__file__).parent.parent / "config" / "bailian_config.json"

    if config_path.exists():
        print(f"Loading config from: {config_path}")
        provider = create_from_config(str(config_path))
    else:
        # Method 2: From environment variables
        print("Config file not found, using environment variables...")
        print("Set BAILIAN_API_URL, BAILIAN_API_KEY, BAILIAN_MODEL")

        try:
            provider = BailianProvider()
        except ValueError as e:
            print(f"❌ Error: {e}")
            print("\n📝 To use Bailian API:")
            print("   1. Copy config/bailian_config.example.json to config/bailian_config.json")
            print("   2. Fill in your API credentials")
            print("   OR")
            print("   1. Set environment variables:")
            print("      export BAILIAN_API_URL='https://...'")
            print("      export BAILIAN_API_KEY='sk-...'")
            print("      export BAILIAN_MODEL='qwen-plus'")
            return 1

    print(f"✓ Bailian Provider initialized")
    print(f"  Model: {provider.model}")
    print(f"  API URL: {provider.api_url}")

    # 2. Initialize components
    print("\n[2/4] Initializing orchestrator...")

    repo_path = Path(__file__).parent.parent / "skills" / "repository"
    repository = SkillRepository(str(repo_path))
    validator = SkillValidator()

    orchestrator = AgentOrchestrator(
        skill_repository=repository,
        skill_validator=validator,
        model_provider=provider  # Use real Bailian API
    )

    print("✓ Orchestrator ready with Bailian API")

    # 3. Run pre-production with real LLM
    print("\n[3/4] Running pre-production with real LLM...")
    print("-" * 70)

    user_input = "我想拍一组自然的个人肖像，用作社交头像，不要看起来像摆拍。"
    print(f"User Input: {user_input}")

    try:
        pre_results = orchestrator.run_pre_production(
            user_input=user_input,
            available_devices=["insta360_link2", "insta360_x4_air"],
            user_level="beginner"
        )

        # Show normalized intent
        if pre_results["intent"].is_successful():
            intent = pre_results["intent"].output
            print(f"\n✓ Intent Normalized (via Bailian):")
            print(f"  Goal Type: {intent['goal_type']}")
            print(f"  Subject Type: {intent['subject_type']}")
            print(f"  Style: {intent.get('style_preference', 'N/A')}")
            print(f"  Output Format: {intent.get('output_format', {}).get('aspect_ratio', 'N/A')}")

        # Show skill retrieval
        if pre_results["bundle"].is_successful():
            bundle = pre_results["bundle"].output
            print(f"\n✓ Skills Retrieved:")
            for skill in bundle['skills']:
                print(f"  - {skill['skill_id']} (v{skill['version']})")

        # Show director plan
        if pre_results["plan"].is_successful():
            plan = pre_results["plan"].output
            print(f"\n✓ Director Plan (via Bailian):")
            print(f"  Creative Goal: {plan['creative_goal']}")
            print(f"  Shot Intentions: {len(plan['shot_intentions'])} stages")

            for intention in plan['shot_intentions'][:3]:  # Show first 3
                print(f"    • {intention['stage']}: {intention['notes']}")

            if plan.get('teaching_notes'):
                print(f"\n  Teaching Notes:")
                for note in plan['teaching_notes'][:2]:  # Show first 2
                    print(f"    📝 {note}")

    except Exception as e:
        print(f"❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # 4. Show API usage stats
    print("\n[4/4] API Usage Statistics")
    print("-" * 70)
    print(f"Total API Calls: {provider.call_count}")
    print(f"Model Used: {provider.model}")

    print("\n" + "=" * 70)
    print("Demo Completed Successfully")
    print("=" * 70)
    print("\n✓ Real Bailian API was used for:")
    print("  - Intent normalization (SkillsManager)")
    print("  - Director planning (Director)")
    print("\n✓ Next steps:")
    print("  - Test Cinematographer with run_filming_step()")
    print("  - Test Editor with run_post_production()")
    print("  - Run complete workflow with real video data")

    return 0


if __name__ == "__main__":
    exit(main())
