import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.skills_manager_agent import SkillManager, SkillsManagerAgent


class StaticProvider:
    def text(self, prompt, expect_json=False):
        return {
            "name": "light-first-observation",
            "name_zh": "以光为先的观察法",
            "description": "Evaluate light before selecting a landscape subject.",
            "description_zh": "先观察光线，再选择主体。",
            "stage": "cinematographer",
            "category": "landscape",
            "tags": ["lighting"],
            "rules": [{"condition": "golden hour", "action": "wait", "reason": "soft light"}],
        }


def test_review_does_not_merge_pending_skill_into_itself(tmp_path, monkeypatch):
    manager = SkillManager(tmp_path)
    agent = SkillsManagerAgent(manager, StaticProvider())
    extracted = agent.author_from_expert("拍自然景色，先看光，再找主体。")
    # Reproduce an index created by an older run where pending metadata was stale.
    manager.index[extracted["skill_id"]]["source"] = "builtin"
    monkeypatch.setattr("builtins.input", lambda _: "合并")

    result = agent.review_and_save(extracted["skill_id"], "personal")

    final_path = Path(result["path"])
    assert result["action"] == "created"
    assert final_path.is_relative_to(tmp_path / "personal")
    assert "pending_review" not in final_path.parts
    assert final_path.exists()
    assert not Path(extracted["pending_path"]).exists()


def test_review_merges_into_repository_skill(tmp_path, monkeypatch):
    manager = SkillManager(tmp_path)
    existing = tmp_path / "builtin" / "cinematographer" / "landscape" / "light.yaml"
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_text(yaml.safe_dump({
        "skill_id": "light",
        "name": "light-first-observation",
        "stage": "cinematographer",
        "category": "landscape",
        "rules": [],
        "tags": [],
    }), encoding="utf-8")
    manager.update_index("light", existing, "cinematographer", "landscape", "builtin")
    agent = SkillsManagerAgent(manager, StaticProvider())
    extracted = agent.author_from_expert("拍自然景色，先看光，再找主体。")
    monkeypatch.setattr("builtins.input", lambda _: "合并")

    result = agent.review_and_save(extracted["skill_id"], "personal")

    assert result["action"] == "merged"
    assert Path(result["path"]) == existing
    assert existing.exists()
    assert not Path(extracted["pending_path"]).exists()
