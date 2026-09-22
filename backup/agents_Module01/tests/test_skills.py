"""
Test skill repository and validator
"""

import pytest
import yaml
from pathlib import Path

from agents_Module.skills import SkillRepository, SkillValidator
from agents_Module.schemas import SkillManifest, SkillStatus, SkillVisibility


def test_repository_load_skill(skill_repository):
    """Test loading skill from repository"""
    # Load action_coach skill
    skill = skill_repository.load_skill("action_coach")

    assert skill is not None
    assert skill.skill_id == "action_coach"
    assert skill.version == "0.1.0"
    assert len(skill.rules) > 0


def test_repository_save_skill(skill_repository):
    """Test saving skill to repository"""
    # Create new skill
    skill_data = {
        "schema_version": "1.0",
        "skill_id": "test_skill",
        "version": "0.1.0",
        "name": "测试技能",
        "name_en": "Test Skill",
        "description": "测试用技能",
        "author": {
            "type": "expert",
            "id": "test_author",
            "display_name": "测试作者",
            "verified": False
        },
        "license": "MIT",
        "visibility": "local",
        "status": "draft",
        "teaching": {
            "audience": "beginner",
            "principles": ["测试原则1"],
            "explain_template": "测试模板"
        },
        "inputs": {
            "intent": {"type": "object"},
            "media_types": ["video"],
            "required_capabilities": []
        },
        "agent_bindings": {
            "director": True,
            "cinematographer": False,
            "editor": False,
            "skills_manager": True
        },
        "rules": [
            {
                "id": "test_rule",
                "when": {
                    "event": "test_event",
                    "confidence_gte": 0.5
                },
                "advice": {
                    "composition": "wide"
                },
                "priority": 50,
                "explanation": "测试规则"
            }
        ],
        "safety": {
            "allowed_actions": ["suggest_composition"],
            "requires_human_approval": [],
            "forbidden_actions": [],
            "min_confidence_for_device_suggestion": 0.7
        },
        "evidence": {
            "examples": [],
            "expert_notes": []
        },
        "tags": ["测试"]
    }

    skill = SkillManifest(**skill_data)
    path = skill_repository.save_skill(skill, location="personal")

    assert path.exists()
    assert "test_skill" in str(path)

    # Load it back
    loaded = skill_repository.load_skill("test_skill")
    assert loaded is not None
    assert loaded.skill_id == "test_skill"


def test_repository_search_by_tag(skill_repository):
    """Test searching skills by tag"""
    results = skill_repository.search(tags=["动作摄影"], max_results=5)

    assert len(results) > 0
    # Should find action_coach
    skill_ids = [s.skill_id for s in results]
    assert "action_coach" in skill_ids


def test_repository_search_by_text(skill_repository):
    """Test text search"""
    results = skill_repository.search(query="旅行", max_results=5)

    assert len(results) > 0
    # Should find travel_story
    skill_ids = [s.skill_id for s in results]
    assert "travel_story" in skill_ids


def test_repository_fork_skill(skill_repository):
    """Test forking a skill"""
    # Fork action_coach
    fork = skill_repository.fork_skill("action_coach", "user123")

    assert fork is not None
    assert fork.skill_id.startswith("action_coach_fork")
    assert fork.version == "0.1.0"
    assert fork.status == SkillStatus.DRAFT
    assert fork.visibility == SkillVisibility.LOCAL
    assert "action_coach@" in fork.parent_skill


def test_validator_basic_validation(skill_validator):
    """Test basic skill validation"""
    skill_data = {
        "schema_version": "1.0",
        "skill_id": "valid_skill",
        "version": "1.0.0",
        "name": "有效技能",
        "name_en": "Valid Skill",
        "description": "有效的技能",
        "author": {
            "type": "expert",
            "id": "author_001",
            "display_name": "作者",
            "verified": False
        },
        "license": "MIT",
        "visibility": "local",
        "status": "draft",
        "teaching": {
            "audience": "beginner",
            "principles": ["原则1"],
            "explain_template": "模板"
        },
        "inputs": {
            "intent": {"type": "object"},
            "media_types": ["video"],
            "required_capabilities": []
        },
        "agent_bindings": {
            "director": True,
            "cinematographer": False,
            "editor": False,
            "skills_manager": False
        },
        "rules": [
            {
                "id": "rule_001",
                "when": {"event": "test", "confidence_gte": 0.5},
                "advice": {"composition": "wide"},
                "priority": 50,
                "explanation": "测试"
            }
        ],
        "safety": {
            "allowed_actions": ["suggest_composition"],
            "requires_human_approval": [],
            "forbidden_actions": [],
            "min_confidence_for_device_suggestion": 0.7
        },
        "evidence": {
            "examples": [],
            "expert_notes": []
        },
        "tags": ["测试"]
    }

    skill = SkillManifest(**skill_data)
    is_valid, errors = skill_validator.validate(skill)

    assert is_valid
    assert len(errors) == 0


def test_validator_forbidden_action(skill_validator):
    """Test validation rejects forbidden actions"""
    skill_data = {
        "schema_version": "1.0",
        "skill_id": "bad_skill",
        "version": "1.0.0",
        "name": "危险技能",
        "name_en": "Dangerous Skill",
        "description": "包含危险动作",
        "author": {
            "type": "expert",
            "id": "author_001",
            "display_name": "作者",
            "verified": False
        },
        "license": "MIT",
        "visibility": "local",
        "status": "draft",
        "teaching": {
            "audience": "beginner",
            "principles": ["原则"],
            "explain_template": "模板"
        },
        "inputs": {
            "intent": {"type": "object"},
            "media_types": ["video"],
            "required_capabilities": []
        },
        "agent_bindings": {
            "director": True,
            "cinematographer": False,
            "editor": False,
            "skills_manager": False
        },
        "rules": [
            {
                "id": "rule_001",
                "when": {"event": "test", "confidence_gte": 0.5},
                "advice": {"composition": "wide"},
                "priority": 50,
                "explanation": "测试"
            }
        ],
        "safety": {
            "allowed_actions": ["delete_media"],  # Forbidden!
            "requires_human_approval": [],
            "forbidden_actions": [],
            "min_confidence_for_device_suggestion": 0.7
        },
        "evidence": {
            "examples": [],
            "expert_notes": []
        },
        "tags": ["测试"]
    }

    skill = SkillManifest(**skill_data)
    is_valid, errors = skill_validator.validate(skill)

    assert not is_valid
    assert len(errors) > 0
    assert any("forbidden" in str(e).lower() for e in errors)


def test_validator_low_confidence(skill_validator):
    """Test validation rejects low confidence threshold"""
    skill_data = {
        "schema_version": "1.0",
        "skill_id": "low_conf_skill",
        "version": "1.0.0",
        "name": "低置信度技能",
        "name_en": "Low Confidence Skill",
        "description": "置信度阈值过低",
        "author": {
            "type": "expert",
            "id": "author_001",
            "display_name": "作者",
            "verified": False
        },
        "license": "MIT",
        "visibility": "local",
        "status": "draft",
        "teaching": {
            "audience": "beginner",
            "principles": ["原则"],
            "explain_template": "模板"
        },
        "inputs": {
            "intent": {"type": "object"},
            "media_types": ["video"],
            "required_capabilities": []
        },
        "agent_bindings": {
            "director": True,
            "cinematographer": False,
            "editor": False,
            "skills_manager": False
        },
        "rules": [],
        "safety": {
            "allowed_actions": ["suggest_composition"],
            "requires_human_approval": [],
            "forbidden_actions": [],
            "min_confidence_for_device_suggestion": 0.3  # Too low!
        },
        "evidence": {
            "examples": [],
            "expert_notes": []
        },
        "tags": ["测试"]
    }

    skill = SkillManifest(**skill_data)
    is_valid, errors = skill_validator.validate(skill)

    assert not is_valid
    assert any("confidence" in str(e).lower() for e in errors)


def test_validator_conflict_detection(skill_validator):
    """Test conflict detection between skills"""
    # Skill 1
    skill1_data = {
        "schema_version": "1.0",
        "skill_id": "skill1",
        "version": "1.0.0",
        "name": "技能1",
        "name_en": "Skill 1",
        "description": "技能1",
        "author": {
            "type": "expert",
            "id": "author_001",
            "display_name": "作者",
            "verified": False
        },
        "license": "MIT",
        "visibility": "local",
        "status": "draft",
        "teaching": {
            "audience": "beginner",
            "principles": ["原则"],
            "explain_template": "模板"
        },
        "inputs": {
            "intent": {"type": "object"},
            "media_types": ["video"],
            "required_capabilities": []
        },
        "agent_bindings": {
            "director": True,
            "cinematographer": False,
            "editor": False,
            "skills_manager": False
        },
        "rules": [
            {
                "id": "rule1",
                "when": {"event": "action_start", "confidence_gte": 0.5},
                "advice": {"composition": "wide"},
                "priority": 80,
                "explanation": "使用广角"
            }
        ],
        "safety": {
            "allowed_actions": ["suggest_composition"],
            "requires_human_approval": [],
            "forbidden_actions": [],
            "min_confidence_for_device_suggestion": 0.7
        },
        "evidence": {
            "examples": [],
            "expert_notes": []
        },
        "tags": ["测试"]
    }

    # Skill 2 - conflicts with skill1
    skill2_data = skill1_data.copy()
    skill2_data["skill_id"] = "skill2"
    skill2_data["name"] = "技能2"
    skill2_data["rules"] = [
        {
            "id": "rule2",
            "when": {"event": "action_start", "confidence_gte": 0.5},  # Same event!
            "advice": {"composition": "full_body"},  # Different advice!
            "priority": 85,
            "explanation": "使用全身"
        }
    ]

    skill1 = SkillManifest(**skill1_data)
    skill2 = SkillManifest(**skill2_data)

    has_conflict, conflicts = skill_validator.check_conflict(skill1, skill2)

    assert has_conflict
    assert len(conflicts) > 0
