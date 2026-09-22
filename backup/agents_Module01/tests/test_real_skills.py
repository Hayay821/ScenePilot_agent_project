"""
Tests using real skills (portrait_story_director, portrait_composition_coach, portrait_reel_editor)
and real test data from project00/data/test_data/
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents_Module.schemas import AgentType, UserLevel
from agents_Module.agents import SkillsManagerAgent, DirectorAgent, CinematographerAgent, EditorAgent
from agents_Module.skills import SkillRepository, SkillValidator
from agents_Module.orchestration import AgentOrchestrator
from agents_Module.providers import MockProvider


@pytest.fixture
def real_skill_repository():
    """Repository with real portrait skills"""
    repo_path = Path(__file__).parent.parent / "skills" / "repository"
    return SkillRepository(str(repo_path))


@pytest.fixture
def real_orchestrator(real_skill_repository):
    """Orchestrator with real skills"""
    validator = SkillValidator()
    provider = MockProvider()
    return AgentOrchestrator(
        skill_repository=real_skill_repository,
        skill_validator=validator,
        model_provider=provider
    )


# Test data paths
TEST_DATA_ROOT = Path(__file__).parent.parent.parent / "data" / "test_data"
TEST_IMG_DIR = TEST_DATA_ROOT / "img"
TEST_VIDEO_DIR = TEST_DATA_ROOT / "video"


class TestRealSkillsLoading:
    """Test that real skills can be loaded correctly"""

    def test_load_portrait_story_director(self, real_skill_repository):
        """Test loading portrait_story_director skill"""
        skill = real_skill_repository.load_skill("portrait_story_director")

        assert skill is not None
        assert skill["skill_id"] == "portrait_story_director"
        assert skill["version"] == "0.1.0"
        assert "director" in skill["agent_binding"]
        assert "teaching" in skill
        assert "rules" in skill
        assert len(skill["rules"]) >= 5

    def test_load_portrait_composition_coach(self, real_skill_repository):
        """Test loading portrait_composition_coach skill"""
        skill = real_skill_repository.load_skill("portrait_composition_coach")

        assert skill is not None
        assert skill["skill_id"] == "portrait_composition_coach"
        assert "cinematographer" in skill["agent_binding"]
        assert "realtime_subject_state_schema" in skill
        assert "device_advice" in skill

    def test_load_portrait_reel_editor(self, real_skill_repository):
        """Test loading portrait_reel_editor skill"""
        skill = real_skill_repository.load_skill("portrait_reel_editor")

        assert skill is not None
        assert skill["skill_id"] == "portrait_reel_editor"
        assert "editor" in skill["agent_binding"]
        assert "timeline_schema" in skill


class TestRealSkillsValidation:
    """Test that real skills pass validation"""

    def test_validate_all_real_skills(self, real_skill_repository):
        """All real skills should pass validation"""
        validator = SkillValidator()

        skills = [
            "portrait_story_director",
            "portrait_composition_coach",
            "portrait_reel_editor"
        ]

        for skill_id in skills:
            skill = real_skill_repository.load_skill(skill_id)
            is_valid, errors = validator.validate(skill)

            assert is_valid, f"{skill_id} validation failed: {errors}"
            assert len(errors) == 0


class TestU001SingleNaturalAvatar:
    """U001: 自然个人肖像用于社交头像"""

    def test_intent_normalization(self, real_orchestrator):
        """Test intent normalization for natural portrait"""
        user_input = "我想拍一组自然的个人肖像，用作社交头像，不要看起来像摆拍。"

        result = real_orchestrator.run_pre_production(
            user_input=user_input,
            available_devices=["insta360_link2", "insta360_x4_air"],
            user_level="beginner"
        )

        assert result["intent"].is_successful()
        intent = result["intent"].output

        assert intent["goal_type"] == "portrait"
        assert intent["subject_type"] == "single_portrait"
        assert "自然" in intent.get("style_preference", "")

    def test_director_plan(self, real_orchestrator):
        """Test director creates plan for natural portrait"""
        user_input = "我想拍一组自然的个人肖像，用作社交头像，不要看起来像摆拍。"

        result = real_orchestrator.run_pre_production(
            user_input=user_input,
            available_devices=["insta360_link2", "insta360_x4_air"],
            user_level="beginner"
        )

        assert result["plan"].is_successful()
        plan = result["plan"].output

        assert "creative_goal" in plan
        assert "priorities" in plan
        assert "shot_intentions" in plan

        # Should avoid forced_pose for natural style
        plan_str = str(plan).lower()
        assert "natural" in plan_str or "自然" in plan_str


class TestU002EnvironmentTravel:
    """U002: 南京户外环境人像"""

    def test_environment_portrait_intent(self, real_orchestrator):
        """Test intent for environmental portrait"""
        user_input = "请拍一个人在南京户外环境中的旅行肖像，要让人看出这个地方，而不是只有一张脸。"

        result = real_orchestrator.run_pre_production(
            user_input=user_input,
            available_devices=["insta360_link2", "insta360_x4_air"],
            user_level="beginner"
        )

        assert result["intent"].is_successful()
        intent = result["intent"].output

        assert intent["subject_type"] == "environmental_portrait"

    def test_environment_uses_x4air(self, real_orchestrator):
        """Environmental portrait should prefer X4 Air for wide context"""
        user_input = "请拍一个人在南京户外环境中的旅行肖像，要让人看出这个地方，而不是只有一张脸。"

        result = real_orchestrator.run_pre_production(
            user_input=user_input,
            available_devices=["insta360_link2", "insta360_x4_air"],
            user_level="beginner"
        )

        assert result["plan"].is_successful()
        plan = result["plan"].output

        # Check if x4air is recommended for environment context
        plan_str = str(plan).lower()
        assert "x4" in plan_str or "air" in plan_str or "environment" in plan_str


class TestU003Interview:
    """U003: 人物采访"""

    def test_interview_intent(self, real_orchestrator):
        """Test interview intent normalization"""
        user_input = "我要录一个人物采访，画面自然、声音清楚，不要因为追求节奏把说话人的停顿都剪掉。"

        result = real_orchestrator.run_pre_production(
            user_input=user_input,
            available_devices=["insta360_link2", "insta360_x4_air"],
            user_level="intermediate"
        )

        assert result["intent"].is_successful()
        intent = result["intent"].output

        assert intent["subject_type"] == "interview"

    def test_interview_preserves_speech(self, real_orchestrator):
        """Interview should preserve natural pauses"""
        user_input = "我要录一个人物采访，画面自然、声音清楚，不要因为追求节奏把说话人的停顿都剪掉。"

        result = real_orchestrator.run_pre_production(
            user_input=user_input,
            available_devices=["insta360_link2", "insta360_x4_air"],
            user_level="intermediate"
        )

        assert result["plan"].is_successful()
        plan = result["plan"].output

        plan_str = str(plan).lower()
        assert "speech" in plan_str or "audio" in plan_str or "sound" in plan_str


class TestU006UserPrefersReaction:
    """U006: 保留人物反应和朋友互动"""

    def test_reaction_priority(self, real_orchestrator):
        """Test that user preference for reactions is captured"""
        user_input = "不要只剪最好看的正脸，我更想保留人物完成动作后笑出来、朋友在旁边反应的画面。"

        result = real_orchestrator.run_pre_production(
            user_input=user_input,
            available_devices=["insta360_link2", "insta360_x4_air"],
            user_level="beginner"
        )

        assert result["intent"].is_successful()
        intent = result["intent"].output

        # Should capture preference for reactions
        intent_str = str(intent).lower()
        assert "reaction" in intent_str or "interaction" in intent_str or "emotional" in intent_str


class TestU007LowConfidence:
    """U007: 用户不确定景别，要求解释方案"""

    def test_explain_mode(self, real_orchestrator):
        """Test that system can provide explanations without execution"""
        user_input = "我不确定该用近景还是全身，你先给我三个方案并解释区别，不要直接执行。"

        result = real_orchestrator.run_pre_production(
            user_input=user_input,
            available_devices=["insta360_link2", "insta360_x4_air"],
            user_level="beginner"
        )

        assert result["intent"].is_successful()
        intent = result["intent"].output

        # Should be in teaching/explanation mode
        assert intent.get("confidence", 1.0) < 0.7 or \
               "explain" in str(intent).lower() or \
               "options" in str(intent).lower()


class TestCinematographerRealtime:
    """Test cinematographer with realistic subject states"""

    def test_subject_lost_recovery(self, real_orchestrator):
        """When subject tracking is lost, should suggest panorama recovery"""
        # First run pre-production
        real_orchestrator.run_pre_production(
            user_input="拍摄个人肖像",
            available_devices=["insta360_link2", "insta360_x4_air"],
            user_level="beginner"
        )

        # Simulate lost tracking
        subject_state = {
            "subject_id": "person_001",
            "bbox_normalized": [0.0, 0.0, 0.0, 0.0],
            "face_visible": False,
            "gaze_direction": "unknown",
            "motion_direction": "unknown",
            "occlusion_ratio": 0.70,
            "tracking_confidence": 0.30
        }

        result = real_orchestrator.run_filming_step(
            current_frame_quality={"exposure": "normal"},
            realtime_subject_state=subject_state
        )

        assert result.is_successful()
        rec = result.output

        # Should suggest panorama recovery
        rec_str = str(rec).lower()
        assert "x4" in rec_str or "air" in rec_str or "panorama" in rec_str or "wide" in rec_str

    def test_gaze_direction_space(self, real_orchestrator):
        """When subject gazes left, should preserve left space"""
        real_orchestrator.run_pre_production(
            user_input="拍摄个人肖像",
            available_devices=["insta360_link2", "insta360_x4_air"],
            user_level="beginner"
        )

        subject_state = {
            "subject_id": "person_001",
            "bbox_normalized": [0.3, 0.2, 0.6, 0.8],
            "face_visible": True,
            "gaze_direction": "left",
            "motion_direction": "still",
            "occlusion_ratio": 0.05,
            "tracking_confidence": 0.92
        }

        result = real_orchestrator.run_filming_step(
            current_frame_quality={"exposure": "normal"},
            realtime_subject_state=subject_state
        )

        assert result.is_successful()
        rec = result.output

        # Should mention left space or composition
        rec_str = str(rec).lower()
        assert "left" in rec_str or "space" in rec_str or "composition" in rec_str


class TestEditorWithEvents:
    """Test editor with realistic event timelines"""

    def test_portrait_timeline_structure(self, real_orchestrator):
        """Test editor creates proper timeline for portrait story"""
        # Run pre-production first
        real_orchestrator.run_pre_production(
            user_input="拍摄自然个人肖像",
            available_devices=["insta360_link2", "insta360_x4_air"],
            user_level="beginner"
        )

        # Simulate captured events
        events = [
            {
                "event_type": "environment_start",
                "timestamp_ms": 0,
                "duration_ms": 3000,
                "camera": "x4air",
                "quality": 0.85
            },
            {
                "event_type": "subject_stable",
                "timestamp_ms": 3000,
                "duration_ms": 5000,
                "camera": "link2",
                "face_quality": 0.90,
                "quality": 0.88
            },
            {
                "event_type": "smile",
                "timestamp_ms": 8000,
                "duration_ms": 2000,
                "camera": "link2",
                "quality": 0.92
            }
        ]

        result = real_orchestrator.run_post_production(
            events=events,
            output_requirements={"aspect_ratio": "1:1", "duration_target_ms": 10000}
        )

        assert result.is_successful()
        timeline = result.output

        assert "timeline" in timeline
        assert len(timeline["timeline"]) >= 3

        # Should have different roles
        roles = [shot.get("role") for shot in timeline["timeline"]]
        assert "environment_context" in roles or "portrait_anchor" in roles


class TestCompleteWorkflowWithRealSkills:
    """Test complete workflow using real skills"""

    def test_complete_portrait_workflow(self, real_orchestrator):
        """Full workflow for natural portrait"""
        # User request
        user_input = "我想拍一组自然的个人肖像，用作社交头像，不要看起来像摆拍。"

        # Run complete workflow
        results = real_orchestrator.run_complete_workflow(
            user_input=user_input,
            available_devices=["insta360_link2", "insta360_x4_air"],
            user_level="beginner",
            events=[
                {"event_type": "environment_start", "timestamp_ms": 0, "duration_ms": 2000, "camera": "x4air"},
                {"event_type": "subject_stable", "timestamp_ms": 2000, "duration_ms": 4000, "camera": "link2", "face_quality": 0.90},
                {"event_type": "smile", "timestamp_ms": 6000, "duration_ms": 2000, "camera": "link2"}
            ],
            output_requirements={"aspect_ratio": "1:1"}
        )

        # Check all stages completed
        assert results["pre_production"]["intent"].is_successful()
        assert results["pre_production"]["bundle"].is_successful()
        assert results["pre_production"]["plan"].is_successful()
        assert results["post_production"].is_successful()

        # Check skills were used
        bundle = results["pre_production"]["bundle"].output
        skill_ids = [s["skill_id"] for s in bundle["skills"]]

        assert "portrait_story_director" in skill_ids
        assert "portrait_composition_coach" in skill_ids
        assert "portrait_reel_editor" in skill_ids
