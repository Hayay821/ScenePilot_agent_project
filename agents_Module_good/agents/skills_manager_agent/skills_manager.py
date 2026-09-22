"""SkillsManager Agent: manages skill selection and expert authoring."""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import yaml


class SkillManager:
    """Loads local English skills and turns Chinese user text into skill context."""

    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root is not None else Path(__file__).resolve().parent.parent.parent / "skills" / "repository"
        self.index_file = self.root / "skill_index.json"
        self._ensure_directories()
        self._load_or_create_index()

    def _ensure_directories(self):
        """Ensure all necessary directories exist."""
        directories = [
            self.root / "builtin" / "common",
            self.root / "builtin" / "director" / "portrait",
            self.root / "builtin" / "director" / "landscape",
            self.root / "builtin" / "director" / "product",
            self.root / "builtin" / "director" / "sports",
            self.root / "builtin" / "cinematographer" / "portrait",
            self.root / "builtin" / "cinematographer" / "landscape",
            self.root / "builtin" / "cinematographer" / "product",
            self.root / "builtin" / "cinematographer" / "sports",
            self.root / "builtin" / "editor" / "portrait",
            self.root / "builtin" / "editor" / "landscape",
            self.root / "builtin" / "editor" / "product",
            self.root / "builtin" / "editor" / "sports",
            self.root / "personal" / "common",
            self.root / "personal" / "director",
            self.root / "personal" / "cinematographer",
            self.root / "personal" / "editor",
            self.root / "pending_review",
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _load_or_create_index(self):
        """Load existing index or create a new one."""
        if self.index_file.exists():
            try:
                self.index = json.loads(self.index_file.read_text(encoding="utf-8"))
            except Exception:
                self.index = {}
        else:
            self.index = {}
            self._rebuild_index()

    def _rebuild_index(self):
        """Rebuild index from all existing YAML files."""
        self.index = {}
        for path in self.root.glob("**/*.yaml"):
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                skill_id = data.get("skill_id") or data.get("id") or path.stem

                # Determine source (builtin/personal/pending_review)
                relative_path = path.relative_to(self.root)
                source = str(relative_path.parts[0]) if relative_path.parts else "unknown"

                # Determine stage and category from path
                stage = None
                category = None
                if len(relative_path.parts) >= 3:
                    stage = str(relative_path.parts[1])
                    category = str(relative_path.parts[2]) if len(relative_path.parts) >= 4 else None

                self.index[skill_id] = {
                    "path": str(relative_path),
                    "stage": stage or self._stage_from_bindings(data),
                    "category": category,
                    "source": source,
                    "last_updated": datetime.now().isoformat()
                }
            except Exception as e:
                print(f"Warning: Failed to index {path}: {e}")

        self._save_index()

    def _save_index(self):
        """Save index to disk."""
        self.index_file.write_text(
            json.dumps(self.index, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def get_skill_path(self, skill_id: str) -> Path | None:
        """Get absolute path for a skill by ID."""
        if skill_id in self.index:
            return self.root / self.index[skill_id]["path"]
        return None

    def update_index(self, skill_id: str, path: Path, stage: str, category: str | None, source: str):
        """Update index with new or modified skill."""
        relative_path = path.relative_to(self.root)
        self.index[skill_id] = {
            "path": str(relative_path),
            "stage": stage,
            "category": category,
            "source": source,
            "last_updated": datetime.now().isoformat()
        }
        self._save_index()

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
        all_skills = self.list()
        stage_skills = []
        for skill in all_skills:
            stages = skill.get("stages", []) or ([skill["stage"]] if skill.get("stage") else [])
            if not stage or stage in stages or skill.get("stage") in {None, "common"}:
                stage_skills.append(skill)
        for skill in stage_skills:
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
        for skill in stage_skills:
            stages = skill.get("stages", []) or ([skill["stage"]] if skill.get("stage") else [])
            if stage in stages:
                fallback.append(skill)
        return [skill for score, skill in scores if score > 0][:3] or fallback[:3]

    def explain(self, skills: list[dict]) -> str:
        return "\n".join(f"- {s['name']}: {s['description']}" for s in skills)

    def draft_from_expert(self, name: str, description: str, rules: list[dict], source_image: str | None = None) -> Path:
        skill_id = "personal_" + uuid.uuid4().hex[:8]
        data = {
            "skill_id": skill_id,
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
        # Save to pending_review directory
        pending_dir = self.root / "pending_review"
        pending_dir.mkdir(parents=True, exist_ok=True)
        path = pending_dir / f"{skill_id}.yaml"
        path.write_text(yaml.safe_dump(data, allow_unicode=False, sort_keys=False), encoding="utf-8")

        # Update index
        self.update_index(skill_id, path, stage="pending", category=None, source="pending_review")

        return path

    def extract_skill_from_text(self, expert_text: str, provider: Any) -> dict:
        """Use LLM to extract structured skill from expert's natural language input.

        Args:
            expert_text: Natural language description from expert photographer
            provider: LLM provider for text generation

        Returns:
            Dictionary with extracted skill information
        """
        prompt = f"""你是一位专业的摄影技能整理专家。一位资深摄影师分享了他的拍摄经验，请将其总结为结构化的拍摄技能（Skill）。

摄影师的经验描述：
{expert_text}

请按照以下 JSON 格式提取技能信息：
{{
  "name": "技能名称（英文，简短）",
  "name_zh": "技能名称（中文）",
  "description": "技能描述（英文，一句话）",
  "description_zh": "技能描述（中文，详细）",
  "stage": "director 或 cinematographer 或 editor 或 common",
  "category": "portrait 或 landscape 或 product 或 sports 或 common",
  "tags": ["相关标签1", "相关标签2"],
  "rules": [
    {{
      "condition": "触发条件（英文）",
      "condition_zh": "触发条件（中文）",
      "action": "建议操作（英文）",
      "action_zh": "建议操作（中文）",
      "reason": "原因说明（中文）"
    }}
  ],
  "confidence": 0.85
}}

注意：
1. stage 表示技能适用阶段：director（拍摄前规划）、cinematographer（实时拍摄）、editor（后期剪辑）、common（通用）
2. category 表示拍摄类型：portrait（人像）、landscape（风景）、product（产品）、sports（运动）、common（通用）
3. rules 是具体的规则列表，每条规则包含触发条件、建议操作和原因
4. 英文字段用于系统处理，中文字段用于向用户展示

只返回 JSON，不要 markdown 代码块。"""

        try:
            result = provider.text(prompt, expect_json=True)
            return result
        except Exception as e:
            print(f"⚠️  LLM 提取失败: {e}")
            # Return a basic structure
            return {
                "name": "expert_skill",
                "name_zh": "专家技能",
                "description": "Expert knowledge from photographer",
                "description_zh": expert_text[:100],
                "stage": "common",
                "category": "common",
                "tags": ["expert"],
                "rules": [],
                "confidence": 0.5,
                "parse_error": True
            }

    def find_similar_skill(self, new_skill: dict, exclude_pending: bool = True) -> tuple[str | None, Path | None]:
        """Find similar existing skill that could be merged.

        Args:
            new_skill: New skill dictionary
            exclude_pending: If True, exclude skills in pending_review (default: True)

        Returns:
            Tuple of (skill_id, path) if found, otherwise (None, None)
        """
        stage = new_skill.get("stage", "common")
        category = new_skill.get("category", "common")
        name = new_skill.get("name", "").lower()

        # Search in index for similar skills
        candidates = []
        for skill_id, info in self.index.items():
            candidate_path = self.root / info["path"]
            # Do not let the item currently under review become its own merge target.
            # Check the path as well as the index metadata because older indexes may
            # contain a stale or incorrect source value.
            is_pending = "pending_review" in candidate_path.parts
            if exclude_pending and (info.get("source") == "pending_review" or is_pending):
                continue

            if info["stage"] == stage and info["category"] == category:
                candidates.append((skill_id, candidate_path))

        # If we found candidates, check names
        for skill_id, path in candidates:
            if path.exists():
                try:
                    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                    existing_name = data.get("name", "").lower()
                    # Simple name similarity check
                    if name in existing_name or existing_name in name:
                        return skill_id, path
                except Exception:
                    continue

        return None, None

    def merge_skill_rules(self, existing_path: Path, new_skill: dict) -> Path:
        """Merge new skill rules into existing YAML file.

        Args:
            existing_path: Path to existing YAML file
            new_skill: New skill data to merge

        Returns:
            Path to updated file
        """
        # Load existing data
        existing_data = yaml.safe_load(existing_path.read_text(encoding="utf-8")) or {}

        # Merge rules (avoid duplicates)
        existing_rules = existing_data.get("rules", [])
        new_rules = new_skill.get("rules", [])

        for new_rule in new_rules:
            # Simple duplicate check by condition
            new_condition = new_rule.get("condition", "")
            is_duplicate = any(
                rule.get("condition", "") == new_condition
                for rule in existing_rules
            )
            if not is_duplicate:
                existing_rules.append(new_rule)

        existing_data["rules"] = existing_rules

        # Update tags (merge unique tags)
        existing_tags = set(existing_data.get("tags", []))
        new_tags = set(new_skill.get("tags", []))
        existing_data["tags"] = list(existing_tags | new_tags)

        # Update timestamp
        existing_data["last_updated"] = datetime.now().isoformat()

        # Save back
        existing_path.write_text(
            yaml.safe_dump(existing_data, allow_unicode=False, sort_keys=False),
            encoding="utf-8"
        )

        return existing_path

    def save_skill(
        self,
        skill_data: dict,
        destination: Literal["personal", "builtin"],
        merge_if_exists: bool = True
    ) -> dict:
        """Save skill to personal or builtin library.

        Args:
            skill_data: Extracted skill data
            destination: "personal" or "builtin"
            merge_if_exists: If True, merge into existing similar skill

        Returns:
            Dictionary with save result
        """
        stage = skill_data.get("stage", "common")
        category = skill_data.get("category", "common")

        # Check for similar existing skill
        if merge_if_exists:
            similar_id, similar_path = self.find_similar_skill(skill_data)
            if similar_path:
                # Merge into existing
                updated_path = self.merge_skill_rules(similar_path, skill_data)

                # Update index timestamp
                if similar_id in self.index:
                    self.index[similar_id]["last_updated"] = datetime.now().isoformat()
                    self._save_index()

                return {
                    "action": "merged",
                    "skill_id": similar_id,
                    "path": str(updated_path),
                    "message_zh": f"已合并到现有技能: {similar_id}"
                }

        # Create new skill
        skill_id = f"{destination}_{uuid.uuid4().hex[:8]}"
        skill_data["skill_id"] = skill_id
        skill_data["id"] = skill_id
        skill_data["status"] = "active"
        skill_data["created_at"] = datetime.now().isoformat()

        # Determine save path
        if stage == "common":
            target_dir = self.root / destination / "common"
        else:
            if category and category != "common":
                target_dir = self.root / destination / stage / category
            else:
                target_dir = self.root / destination / stage

        target_dir.mkdir(parents=True, exist_ok=True)
        save_path = target_dir / f"{skill_id}.yaml"

        # Save YAML
        save_path.write_text(
            yaml.safe_dump(skill_data, allow_unicode=False, sort_keys=False),
            encoding="utf-8"
        )

        # Update index
        self.update_index(skill_id, save_path, stage, category, destination)

        return {
            "action": "created",
            "skill_id": skill_id,
            "path": str(save_path),
            "message_zh": f"已创建新技能: {skill_id}"
        }


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
            "matched_skills": selected,
            "explanation_zh": self.skills.explain(selected),
            "next": "confirm skills or continue"
        }

    def author_from_expert(self, expert_text: str) -> dict:
        """Extract skill from expert's natural language input.

        Args:
            expert_text: Natural language description from expert photographer

        Returns:
            Dictionary with extracted skill and pending review status
        """
        print("\n" + "="*60)
        print("🎓 SkillsManager - 专家技能提取")
        print("="*60)
        print(f"正在分析专家输入...\n")

        # Use LLM to extract structured skill
        extracted = self.skills.extract_skill_from_text(expert_text, self.provider)

        if extracted.get("parse_error"):
            print("⚠️  自动提取失败，使用基础结构")

        # Display extracted skill to user
        print("✅ 提取的技能信息：")
        print(f"  名称: {extracted.get('name_zh', 'N/A')} ({extracted.get('name', 'N/A')})")
        print(f"  描述: {extracted.get('description_zh', 'N/A')}")
        print(f"  阶段: {extracted.get('stage', 'common')}")
        print(f"  类型: {extracted.get('category', 'common')}")
        print(f"  标签: {', '.join(extracted.get('tags', []))}")
        print(f"  规则数量: {len(extracted.get('rules', []))}")

        # Display rules
        rules = extracted.get('rules', [])
        if rules:
            print("\n  规则详情:")
            for idx, rule in enumerate(rules, 1):
                print(f"    {idx}. 条件: {rule.get('condition_zh', rule.get('condition', 'N/A'))}")
                print(f"       操作: {rule.get('action_zh', rule.get('action', 'N/A'))}")
                if rule.get('reason'):
                    print(f"       原因: {rule.get('reason')}")

        print("="*60 + "\n")

        # Save to pending_review
        skill_id = f"pending_{uuid.uuid4().hex[:8]}"
        extracted["skill_id"] = skill_id
        extracted["id"] = skill_id
        extracted["status"] = "pending_review"
        extracted["created_at"] = datetime.now().isoformat()

        pending_dir = self.skills.root / "pending_review"
        pending_dir.mkdir(parents=True, exist_ok=True)
        pending_path = pending_dir / f"{skill_id}.yaml"

        pending_path.write_text(
            yaml.safe_dump(extracted, allow_unicode=False, sort_keys=False),
            encoding="utf-8"
        )

        # Update index
        self.skills.update_index(
            skill_id,
            pending_path,
            stage=extracted.get("stage", "common"),
            category=extracted.get("category"),
            source="pending_review"
        )

        return {
            "skill_id": skill_id,
            "skill_data": extracted,
            "pending_path": str(pending_path),
            "status": "pending_review",
            "message_zh": "技能已提取并保存到待审核目录"
        }

    def review_and_save(
        self,
        skill_id: str,
        destination: Literal["personal", "builtin", "cancel"]
    ) -> dict:
        """Review and save pending skill to final destination.

        Args:
            skill_id: ID of the pending skill
            destination: "personal", "builtin", or "cancel"

        Returns:
            Dictionary with save result
        """
        print("\n" + "="*60)
        print("📋 SkillsManager - 技能审核")
        print("="*60)

        # Load pending skill
        skill_path = self.skills.get_skill_path(skill_id)
        if not skill_path or not skill_path.exists():
            return {
                "status": "error",
                "message_zh": f"未找到待审核技能: {skill_id}"
            }

        skill_data = yaml.safe_load(skill_path.read_text(encoding="utf-8"))

        if destination == "cancel":
            # Delete pending skill
            skill_path.unlink()
            if skill_id in self.skills.index:
                del self.skills.index[skill_id]
                self.skills._save_index()

            print("❌ 已取消该技能\n")
            return {
                "status": "cancelled",
                "message_zh": "技能已取消"
            }

        # Check for similar existing skills
        similar_id, similar_path = self.skills.find_similar_skill(skill_data)

        if similar_path:
            print(f"💡 发现相似的现有技能: {similar_id}")
            print(f"   路径: {similar_path}")
            print(f"\n是否合并到现有技能？")
            print("   - 合并: 将新规则添加到现有技能")
            print("   - 新建: 创建独立的新技能")
            merge_choice = input("\n请选择 [合并/新建]: ").strip().lower()

            if merge_choice in ["合并", "merge", "m"]:
                result = self.skills.save_skill(skill_data, destination, merge_if_exists=True)
            else:
                result = self.skills.save_skill(skill_data, destination, merge_if_exists=False)
        else:
            # No similar skill, create new
            print("✨ 未找到相似技能，将创建新技能")
            result = self.skills.save_skill(skill_data, destination, merge_if_exists=False)

        # Remove the pending copy only after the final repository write succeeded.
        # If saving raises, leave it in place so the review can be retried.
        skill_path.unlink()
        if skill_id in self.skills.index:
            del self.skills.index[skill_id]
            self.skills._save_index()

        print(f"\n✅ {result['message_zh']}")
        print(f"   最终路径: {result['path']}")
        print("="*60 + "\n")

        return result

    def author(self, name: str, description: str, rules: list[dict], source_image: str | None = None) -> dict:
        """Legacy method for programmatic skill authoring."""
        path = self.skills.draft_from_expert(name, description, rules, source_image)
        return {
            "status": "draft_saved_local",
            "path": str(path),
            "message_zh": "已生成本地 Skill 草案，请专家确认后再使用。"
        }
