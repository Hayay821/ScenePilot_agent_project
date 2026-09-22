import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fast import MediaTools, ScenePilotFast, SkillManager


def test_skills_are_english_and_selectable():
    manager = SkillManager()
    skills = manager.select("portrait director", "director")
    assert skills
    assert all(skill.get("id") for skill in skills)
    assert all(skill.get("stage") for skill in skills)
    assert all(skill.get("rules") for skill in skills)


def test_director_and_filming_mock(tmp_path):
    app = ScenePilotFast("mock")
    result = app.director.run("拍摄自然人像", app.skills.select("portrait", "director"), [])
    assert result["shot_plan"]
    frame = tmp_path / "frame.jpg"
    frame.write_bytes(b"not a real image")
    filming = app.cinematographer.run([str(frame)], [], "拍一张")
    assert filming["suggestion"]["action"] == "capture_frame"


def test_expert_skill_draft_is_saved_locally(tmp_path, monkeypatch):
    monkeypatch.setattr("fast.SKILLS_DIR", tmp_path)
    manager = SkillManager(tmp_path)
    path = manager.draft_from_expert("My Portrait Rule", "Keep gaze space", [{"condition": "gaze_left", "advice": "leave_left_space"}])
    data = path.read_text(encoding="utf-8")
    assert "status: draft" in data
    assert "language: en" in data


def test_media_image_discovery(tmp_path):
    (tmp_path / "a.jpg").write_bytes(b"x")
    (tmp_path / "b.txt").write_text("x")
    assert len(MediaTools.images(tmp_path)) == 1
