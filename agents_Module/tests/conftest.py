"""
Test fixtures for agent module
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
import tempfile
import shutil

from agents_Module.skills import SkillRepository, SkillValidator
from agents_Module.providers import MockProvider
from agents_Module.orchestration import AgentOrchestrator


@pytest.fixture
def temp_skill_dir():
    """Create temporary skill directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def skill_repository(temp_skill_dir):
    """Create skill repository with example skills"""
    repo = SkillRepository(temp_skill_dir)

    # Load example skills from examples/
    examples_dir = Path(__file__).parent.parent / "skills" / "examples"

    if examples_dir.exists():
        for skill_file in examples_dir.glob("*.yaml"):
            import yaml
            from agents_Module.schemas import SkillManifest

            with open(skill_file, "r", encoding="utf-8") as f:
                skill_data = yaml.safe_load(f)

            skill = SkillManifest(**skill_data)
            repo.save_skill(skill, location="personal")

    return repo


@pytest.fixture
def skill_validator():
    """Create skill validator"""
    return SkillValidator()


@pytest.fixture
def mock_provider():
    """Create mock model provider"""
    return MockProvider()


@pytest.fixture
def orchestrator(skill_repository, skill_validator, mock_provider, temp_skill_dir):
    """Create agent orchestrator"""
    audit_log = Path(temp_skill_dir) / "audit.jsonl"

    return AgentOrchestrator(
        skill_repository=skill_repository,
        skill_validator=skill_validator,
        model_provider=mock_provider,
        audit_log_path=str(audit_log),
    )


@pytest.fixture
def sample_intent():
    """Sample normalized intent"""
    return {
        "intent_id": "intent_test_001",
        "session_id": "session_test",
        "raw_input": "我想拍一个动作挑战视频",
        "goal": {
            "goal_type": "action_story",
            "subject": "single_person",
            "priority": ["action_clarity", "peak_moment", "reaction"],
            "style": "热血"
        },
        "output": {
            "duration_sec": 30,
            "ratio": "9:16",
            "format": "mp4",
            "quality": "high"
        },
        "skill_query": {
            "tags": ["动作摄影"],
            "agents": ["director", "cinematographer"],
            "devices": ["link2", "x4air"],
            "max_results": 3
        },
        "user_level": "beginner",
        "teaching_mode": True,
        "available_devices": ["link2", "x4air"],
        "device_preferences": {},
        "constraints": {},
        "created_at": "2026-09-22T00:00:00",
        "confidence": 0.85
    }


@pytest.fixture
def sample_subject():
    """Sample subject state"""
    return {
        "id": "person_1",
        "type": "person",
        "bbox": [0.30, 0.20, 0.25, 0.65],
        "confidence": 0.92,
        "motion_vector": [0.1, 0.0],
        "pose": "standing"
    }


@pytest.fixture
def sample_events():
    """Sample detected events"""
    return [
        {
            "event_id": "evt_001",
            "event_type": "action_start",
            "start_ms": 1000,
            "end_ms": 2000,
            "confidence": 0.88,
            "subject_id": "person_1",
            "metadata":{}
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
