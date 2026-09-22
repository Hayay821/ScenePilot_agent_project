"""
Quick test script to verify installation and imports
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_imports():
    """Test that all modules can be imported"""

    print("Testing imports...")
    print()

    try:
        print("✓ Importing schemas...")
        from agents_Module.schemas import (
            AgentType, AgentResult, UserLevel,
            NormalizedIntent, DirectorPlan,
            CinematographerRecommendation, EditPlan
        )

        print("✓ Importing skills...")
        from agents_Module.skills import SkillRepository, SkillValidator

        print("✓ Importing agents...")
        from agents_Module.agents import (
            BaseAgent, SkillsManagerAgent,
            DirectorAgent, CinematographerAgent, EditorAgent
        )

        print("✓ Importing providers...")
        from agents_Module.providers import MockProvider, BailianProvider

        print("✓ Importing orchestration...")
        from agents_Module.orchestration import AgentOrchestrator

        print()
        print("=" * 50)
        print("✓ All imports successful!")
        print("=" * 50)
        return True

    except ImportError as e:
        print()
        print("=" * 50)
        print(f"❌ Import failed: {e}")
        print("=" * 50)
        return False

def test_basic_functionality():
    """Test basic functionality"""

    print()
    print("Testing basic functionality...")
    print()

    try:
        from agents_Module.providers import MockProvider
        from agents_Module.skills import SkillRepository, SkillValidator
        from agents_Module.orchestration import AgentOrchestrator

        # Initialize components
        repo_path = Path(__file__).parent.parent / "skills" / "repository"

        print(f"✓ Repository path: {repo_path}")

        repo = SkillRepository(str(repo_path))
        validator = SkillValidator()
        provider = MockProvider()

        print("✓ Components initialized")

        orchestrator = AgentOrchestrator(
            skill_repository=repo,
            skill_validator=validator,
            model_provider=provider
        )

        print("✓ Orchestrator created")

        # Run simple workflow
        result = orchestrator.run_pre_production(
            user_input="测试拍摄",
            devices=["osmo_pocket_3"],
            user_level="beginner"
        )

        print(f"✓ Workflow executed: session {result['session_id'][:8]}...")

        print()
        print("=" * 50)
        print("✓ Basic functionality working!")
        print("=" * 50)
        return True

    except Exception as e:
        print()
        print("=" * 50)
        print(f"❌ Functionality test failed: {e}")
        print("=" * 50)
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""

    print("=" * 50)
    print("agents_Module - Quick Test")
    print("=" * 50)
    print()

    # Test imports
    imports_ok = test_imports()

    if not imports_ok:
        print()
        print("Please check:")
        print("1. Python path is correct")
        print("2. All dependencies installed: pip install -r requirements.txt")
        print("3. All __init__.py files exist")
        sys.exit(1)

    # Test functionality
    functionality_ok = test_basic_functionality()

    if not functionality_ok:
        print()
        print("Please check:")
        print("1. Skills repository exists")
        print("2. All agent modules are implemented")
        sys.exit(1)

    print()
    print("=" * 50)
    print("✓ ALL TESTS PASSED!")
    print("=" * 50)
    print()
    print("Next steps:")
    print("1. Run full test suite: pytest tests/ -v")
    print("2. Run examples: python examples/complete_workflow.py")
    print("3. Use CLI: python -m agents_Module list")

if __name__ == "__main__":
    main()
