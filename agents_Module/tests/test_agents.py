"""
Test individual agents
"""

import pytest
from agents_Module.agents import (
    SkillsManagerAgent,
    DirectorAgent,
    CinematographerAgent,
    EditorAgent,
)
from agents_Module.schemas import AgentType


def test_skills_manager_normalize_intent(
    skill_repository,
    skill_validator,
    mock_provider
):
    """Test intent normalization"""
    agent = SkillsManagerAgent(
        skill_repository=skill_repository,
        skill_validator=skill_validator,
        model_provider=mock_provider
    )

    result = agent.process({
        "task": "normalize_intent",
        "user_input": "我想拍摄一个动作挑战视频",
        "session_id": "test_session",
        "available_devices": ["link2", "x4air"],
        "user_level": "beginner"
    })

    assert result.agent_name == AgentType.SKILLS_MANAGER
    assert result.is_successful()
    assert "intent_id" in result.output
    assert result.output["goal"]["goal_type"] == "action_story"


def test_skills_manager_retrieve_skills(
    skill_repository,
    skill_validator,
    sample_intent
):
    """Test skill retrieval"""
    agent = SkillsManagerAgent(
        skill_repository=skill_repository,
        skill_validator=skill_validator
    )

    result = agent.process({
        "task": "retrieve_skills",
        "intent": sample_intent,
        "session_id": "test_session"
    })

    assert result.is_successful()
    assert "skills" in result.output
    # Should find action_coach skill
    assert len(result.output["skills"]) > 0


def test_skills_manager_create_bundle(
    skill_repository,
    skill_validator,
    sample_intent
):
    """Test bundle creation"""
    agent = SkillsManagerAgent(
        skill_repository=skill_repository,
        skill_validator=skill_validator
    )

    # First retrieve skills
    skills_result = agent.process({
        "task": "retrieve_skills",
        "intent": sample_intent,
        "session_id": "test_session"
    })

    # Then create bundle
    result = agent.process({
        "task": "create_bundle",
        "skills": skills_result.output["skills"],
        "intent_id": sample_intent["intent_id"],
        "session_id": "test_session"
    })

    assert result.is_successful()
    assert "bundle_id" in result.output
    assert len(result.output["skills"]) > 0


def test_director_create_plan(sample_intent, mock_provider):
    """Test director plan creation"""
    agent = DirectorAgent(model_provider=mock_provider)

    # Mock skill bundle
    skill_bundle = {
        "bundle_id": "bundle_test",
        "skills": [{
            "skill_id": "action_coach",
            "rules": [
                {
                    "id": "action_peak",
                    "priority": 100,
                    "explanation": "动作高潮是主要节点"
                }
            ]
        }]
    }

    result = agent.process({
        "intent": sample_intent,
        "skill_bundle": skill_bundle,
        "session_id": "test_session"
    })

    assert result.agent_name == AgentType.DIRECTOR
    assert result.is_successful()
    assert "priorities" in result.output
    assert "shot_intentions" in result.output
    assert len(result.output["shot_intentions"]) > 0


def test_cinematographer_recommendation(sample_subject, mock_provider):
    """Test cinematographer recommendation"""
    agent = CinematographerAgent(model_provider=mock_provider)

    # Mock plan
    plan = {
        "plan_id": "plan_test",
        "intent_id": "intent_test",
        "shot_intentions": [
            {
                "stage": "main",
                "camera": "link2",
                "style": "full_body_tracking",
                "duration_hint_sec": 5.0
            }
        ]
    }

    result = agent.process({
        "plan": plan,
        "subject": sample_subject,
        "timestamp_ms": 5000,
        "session_id": "test_session",
        "current_stage": "main"
    })

    assert result.agent_name == AgentType.CINEMATOGRAPHER
    assert result.is_successful()
    assert "shot_strategy" in result.output
    assert "suggested_actions" in result.output


def test_editor_create_timeline(sample_intent, sample_events, mock_provider):
    """Test editor timeline creation"""
    agent = EditorAgent(model_provider=mock_provider)

    # Mock plan
    plan = {
        "plan_id": "plan_test",
        "intent_id": sample_intent["intent_id"],
        "skill_bundle_id": "bundle_test",
        "shot_intentions": [
            {
                "stage": "prepare",
                "camera": "x4air",
                "duration_hint_sec": 3.0,
                "notes": "准备阶段"
            },
            {
                "stage": "main",
                "camera": "link2",
                "duration_hint_sec": 10.0,
                "notes": "主要内容"
            }
        ]
    }

    result = agent.process({
        "plan": plan,
        "events": sample_events,
        "media_sources": [
            {"source_id": "x4air_001", "duration_ms": 5000},
            {"source_id": "link2_001", "duration_ms": 12000}
        ],
        "intent": sample_intent,
        "session_id": "test_session"
    })

    assert result.agent_name == AgentType.EDITOR
    assert result.is_successful()
    assert "timeline" in result.output
    assert len(result.output["timeline"]) > 0
    assert result.output["total_duration_ms"] > 0


def test_agent_teaching_notes(skill_repository, skill_validator):
    """Test teaching notes generation"""
    agent = SkillsManagerAgent(
        skill_repository=skill_repository,
        skill_validator=skill_validator
    )

    result = agent.process({
        "task": "normalize_intent",
        "user_input": "拍摄旅行视频",
        "session_id": "test_session",
        "available_devices": ["link2", "x4air"],
        "user_level": "beginner"
    })

    # Beginner mode should have teaching notes
    assert result.teaching_notes is not None
    assert len(result.teaching_notes) > 0
