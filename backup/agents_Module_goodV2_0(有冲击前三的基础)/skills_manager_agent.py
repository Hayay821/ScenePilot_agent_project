"""SkillsManager Agent: manages skill selection and expert authoring."""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import yaml


class SkillManager:
    """Loads local English skills and turns Chinese user text into skill context."""

    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root is not None else Path(__file__).resolve().parent / "skills" / "repository"

    def list(self) -> list[dict]:
        skills = []
        for path in self.root.glob("**/*.yaml"):
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            data["_path"] = str(path)
            data.setdefault("id", data.get("skill_id", path.stem))
            data.setdefault("stage", self._stage_from_bindings(data))
            data.setdefault("tags", [])
            skills.append(data)
        return skills

    @staticmethod
    def _stage_from_bindings(skill: dict) -> str | None:
        bindings = skill.get("agent_bindings", {})
        for agent in ("director", "cinematographer", "editor"):
            if bindings.get(agent):
                return agent
        return None

    def select(self, user_text: str, stage: str | None = None) -> list[dict]:
        text = user_text.lower()
        aliases = {
            "人像": "portrait", "肖像": "portrait", "人物": "portrait",
            "导演": "directing", "拍摄前": "directing", "构图": "composition",
            "摄影": "cinematographer", "跟拍": "tracking", "实时": "realtime",
            "剪辑": "editing", "视频": "editing", "成片": "editing",
            "故事": "story", "反应": "reaction",
        }
        for source, target in aliases.items():
            if source in text:
                text += " " + target
        scores = []
        for skill in self.list():
            tags = " ".join(skill.get("tags", [])).lower()
            stages = skill.get("stages", []) or ([skill["stage"]] if skill.get("stage") else [])
            score = sum(1 for word in tags.split() if word in text)
            if stage in stages:
                score += 3
            if not score and stage in stages:
                score = 1
            scores.append((score, skill))
        scores.sort(key=lambda item: item[0], reverse=True)
        fallback = []
        for skill in self.list():
            stages = skill.get("stages", []) or ([skill["stage"]] if skill.get("stage") else [])
            if stage in stages:
                fallback.append(skill)
        return [skill for score, skill in scores if score > 0][:3] or fallback[:3]

    def explain(self, skills: list[dict]) -> str:
        return "\n".join(f"- {s['name']}: {s['description']}" for s in skills)

    def draft_from_expert(self, name: str, description: str, rules: list[dict], source_image: str | None = None) -> Path:
        skill_id = "personal_" + uuid.uuid4().hex[:8]
        data = {
            "id": skill_id,
            "name": name,
            "description": description,
            "language": "en",
            "author": "expert",
            "status": "draft",
            "stages": ["director", "cinematographer", "editor"],
            "tags": ["expert", "portrait"],
            "rules": rules,
            "source_image": source_image,
        }
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / f"{skill_id}.yaml"
        path.write_text(yaml.safe_dump(data, allow_unicode=False, sort_keys=False), encoding="utf-8")
        return path


class SkillsManagerAgent:
    """Agent that manages skills and interacts with users about skill selection."""

    def __init__(self, skills: SkillManager, provider: Any):
        self.skills = skills
        self.provider = provider

    def interact(self, user_text: str, stage: str) -> dict:
        selected = self.skills.select(user_text, stage)
        return {
            "user_text": user_text,
            "stage": stage,
            "skills": selected,
            "explanation_zh": self.skills.explain(selected),
            "next": "confirm skills or continue"
        }

    def author(self, name: str, description: str, rules: list[dict], source_image: str | None = None) -> dict:
        path = self.skills.draft_from_expert(name, description, rules, source_image)
        return {
            "status": "draft_saved_local",
            "path": str(path),
            "message_zh": "已生成本地 Skill 草案，请专家确认后再使用。"
        }
