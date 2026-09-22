"""
Test complete workflow orchestration
"""

import pytest
from agents_Module.orchestration import AgentOrchestrator, WorkflowStage


def test_pre_production_workflow(orchestrator):
    """Test pre-production workflow"""
    user_input = "我想拍一个动作挑战视频，记录完整的动作过程"

    results = orchestrator.run_pre_production(
        user_input=user_input,
        available_devices=["link2", "x4air"],
        user_level="beginner"
    )

    # Check all steps completed
    assert "intent" in results
    assert "skills" in results
    assert "bundle" in results
    assert "plan" in results

    # Check intent normalization
    intent_result = results["intent"]
    assert intent_result.is_successful()
    assert intent_result.output["goal"]["goal_type"] == "action_story"

    # Check skills retrieved
    skills_result = results["skills"]
    assert skills_result.is_successful()
    assert len(skills_result.output["skills"]) > 0

    # Check bundle created
    bundle_result = results["bundle"]
    assert bundle_result.is_successful()

    # Check plan created
    plan_result = results["plan"]
    assert plan_result.is_successful()
    assert "priorities" in plan_result.output
    assert "shot_intentions" in plan_result.output


def test_filming_step(orchestrator, sample_subject):
    """Test single filming step"""
    # First run pre-production
    orchestrator.run_pre_production(
        user_input="拍摄动作视频",
        available_devices=["link2", "x4air"]
    )

    # Then run filming step
    rec_result = orchestrator.run_filming_step(
        subject=sample_subject,
        timestamp_ms=5000,
        current_stage="main"
    )

    assert rec_result.is_successful()
    assert "shot_strategy" in rec_result.output
    assert "suggested_actions" in rec_result.output


def test_post_production_workflow(orchestrator, sample_events):
    """Test post-production workflow"""
    # First run pre-production
    orchestrator.run_pre_production(
        user_input="拍摄动作视频",
        available_devices=["link2", "x4air"]
    )

    # Then run post-production
    edit_result = orchestrator.run_post_production(
        events=sample_events,
        media_sources=[
            {"source_id": "x4air_001", "duration_ms": 10000},
            {"source_id": "link2_001", "duration_ms": 8000}
        ]
    )

    assert edit_result.is_successful()
    assert "timeline" in edit_result.output
    assert len(edit_result.output["timeline"]) > 0


def test_complete_workflow(orchestrator, sample_events):
    """Test complete workflow from intent to edit"""
    results = orchestrator.run_complete_workflow(
        user_input="拍摄团队庆祝视频",
        available_devices=["link2", "x4air"],
        user_level="intermediate",
        events=sample_events,
        media_sources=[
            {"source_id": "x4air_001", "duration_ms": 15000},
            {"source_id": "link2_001", "duration_ms": 12000}
        ]
    )

    # Check all stages completed
    assert "intent" in results
    assert "plan" in results
    assert "edit" in results

    # Check final edit plan
    edit_result = results["edit"]
    assert edit_result.is_successful()
    assert edit_result.output["total_duration_ms"] > 0


def test_session_management(orchestrator):
    """Test session state management"""
    # Initial state
    summary = orchestrator.get_session_summary()
    assert summary["results_count"] == 0
    assert not summary["has_intent"]
    assert not summary["has_plan"]

    # After pre-production
    orchestrator.run_pre_production(
        user_input="测试视频",
        available_devices=["link2"]
    )

    summary = orchestrator.get_session_summary()
    assert summary["results_count"] > 0
    assert summary["has_intent"]
    assert summary["has_plan"]

    # Reset session
    old_session_id = orchestrator.session_id
    orchestrator.reset_session()

    assert orchestrator.session_id != old_session_id
    assert len(orchestrator.results) == 0


def test_audit_logging(orchestrator, tmp_path):
    """Test audit log creation"""
    # Run workflow
    orchestrator.run_pre_production(
        user_input="测试审计日志",
        available_devices=["link2", "x4air"]
    )

    # Check audit log exists
    if orchestrator.audit_log_path:
        assert orchestrator.audit_log_path.exists()

        # Read log
        with open(orchestrator.audit_log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        assert len(lines) > 0

        # Parse first entry
        import json
        entry = json.loads(lines[0])
        assert "timestamp" in entry
        assert "agent" in entry
        assert "result_id" in entry


def test_error_handling_missing_plan(orchestrator):
    """Test error when filming without plan"""
    with pytest.raises(RuntimeError, match="Must run pre_production"):
        orchestrator.run_filming_step(
            subject={"id": "person_1"},
            timestamp_ms=0
        )


def test_error_handling_missing_intent(orchestrator):
    """Test error when post-production without pre-production"""
    with pytest.raises(RuntimeError, match="Must run pre_production"):
        orchestrator.run_post_production(events=[])
