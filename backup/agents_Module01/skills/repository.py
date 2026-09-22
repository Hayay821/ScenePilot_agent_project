"""
Skill Repository

Local skill storage and retrieval.
"""

import yaml
import json
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..schemas import SkillManifest, SkillStatus, SkillVisibility


class SkillRepository:
    """
    Local skill repository

    Manages skill storage, versioning, and retrieval.
    """

    def __init__(self, base_path: str):
        """
        Initialize repository

        Args:
            base_path: Base directory for skills storage
        """
        self.base_path = Path(base_path)
        self.builtin_path = self.base_path / "builtin"
        self.community_path = self.base_path / "community"
        self.personal_path = self.base_path / "personal"
        self.pending_path = self.base_path / "pending_review"
        self.deprecated_path = self.base_path / "deprecated"

        # Create directories
        for path in [
            self.builtin_path,
            self.community_path,
            self.personal_path,
            self.pending_path,
            self.deprecated_path,
        ]:
            path.mkdir(parents=True, exist_ok=True)

    def load_skill(self, skill_id: str, version: Optional[str] = None) -> Optional[SkillManifest]:
        """
        Load skill by ID

        Args:
            skill_id: Skill identifier
            version: Specific version (None for latest)

        Returns:
            SkillManifest or None if not found
        """
        # Search all locations
        for search_path in [
            self.builtin_path,
            self.community_path,
            self.personal_path,
            self.pending_path,
        ]:
            # First try direct file: builtin/agent_type/skill_id.yaml (flat structure)
            for agent_dir in ["director", "cinematographer", "editor", "skills_manager"]:
                flat_path = search_path / agent_dir / f"{skill_id}.yaml"
                if flat_path.exists():
                    return self._load_from_file(flat_path)

            # Also try direct file without agent subdirectory
            direct_path = search_path / f"{skill_id}.yaml"
            if direct_path.exists():
                return self._load_from_file(direct_path)

            # Fall back to versioned structure: skill_id/version/skill.yaml
            skill_path = search_path / skill_id
            if not skill_path.exists():
                continue

            # Find version
            if version:
                version_path = skill_path / version / "skill.yaml"
            else:
                # Get latest version
                versions = sorted(
                    [v.name for v in skill_path.iterdir() if v.is_dir()],
                    reverse=True
                )
                if not versions:
                    continue
                version_path = skill_path / versions[0] / "skill.yaml"

            if version_path.exists():
                return self._load_from_file(version_path)

        return None

    def _load_from_file(self, path: Path) -> SkillManifest:
        """Load skill from YAML file"""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Compute content hash
        content_str = json.dumps(data, sort_keys=True)
        content_hash = hashlib.sha256(content_str.encode()).hexdigest()[:16]
        data["content_hash"] = content_hash

        return SkillManifest(**data)

    def save_skill(self, skill: SkillManifest, location: str = "personal") -> Path:
        """
        Save skill to repository

        Args:
            skill: Skill manifest to save
            location: Storage location: builtin, community, personal, pending_review

        Returns:
            Path where skill was saved
        """
        # Determine base path
        location_map = {
            "builtin": self.builtin_path,
            "community": self.community_path,
            "personal": self.personal_path,
            "pending_review": self.pending_path,
            "deprecated": self.deprecated_path,
        }

        base = location_map.get(location, self.personal_path)

        # Create directory structure
        skill_dir = base / skill.skill_id / skill.version
        skill_dir.mkdir(parents=True, exist_ok=True)

        # Save skill.yaml
        skill_path = skill_dir / "skill.yaml"

        # Convert to dict and clean up
        data = skill.model_dump(exclude_none=True)

        # Update timestamps
        now = datetime.utcnow().isoformat()
        if not data.get("created_at"):
            data["created_at"] = now
        data["updated_at"] = now

        # Compute content hash
        content_str = json.dumps(data, sort_keys=True)
        data["content_hash"] = hashlib.sha256(content_str.encode()).hexdigest()[:16]

        with open(skill_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)

        return skill_path

    def search(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        agent: Optional[str] = None,
        device: Optional[str] = None,
        status: Optional[SkillStatus] = None,
        visibility: Optional[SkillVisibility] = None,
        max_results: int = 10,
    ) -> List[SkillManifest]:
        """
        Search for skills

        Args:
            query: Text query
            tags: Filter by tags
            agent: Filter by agent compatibility
            device: Filter by device support
            status: Filter by status
            visibility: Filter by visibility
            max_results: Maximum number of results

        Returns:
            List of matching skills
        """
        import sys
        print(f"\n[SEARCH DEBUG] Starting search with:", file=sys.stderr)
        print(f"  tags={tags}", file=sys.stderr)
        print(f"  agent={agent}", file=sys.stderr)
        print(f"  max_results={max_results}", file=sys.stderr)

        results = []
        seen_skill_ids = set()

        # Search all locations
        for search_path in [
            self.builtin_path,
            self.community_path,
            self.personal_path,
            self.pending_path,
        ]:
            if not search_path.exists():
                continue

            # Method 1: Flat structure - look for agent subdirectories with .yaml files
            for agent_dir in ["director", "cinematographer", "editor", "skills_manager"]:
                agent_path = search_path / agent_dir
                if agent_path.exists() and agent_path.is_dir():
                    print(f"[SEARCH DEBUG] Checking {agent_path}", file=sys.stderr)
                    for skill_file in agent_path.glob("*.yaml"):
                        if skill_file.is_file():
                            print(f"[SEARCH DEBUG] Found skill file: {skill_file.name}", file=sys.stderr)
                            try:
                                skill = self._load_from_file(skill_file)
                                print(f"[SEARCH DEBUG] Loaded skill: {skill.skill_id}, tags={skill.tags}", file=sys.stderr)

                                # Skip duplicates
                                if skill.skill_id in seen_skill_ids:
                                    continue

                                # Apply filters
                                if status and skill.status != status:
                                    print(f"[SEARCH DEBUG] Filtered by status", file=sys.stderr)
                                    continue
                                if visibility and skill.visibility != visibility:
                                    print(f"[SEARCH DEBUG] Filtered by visibility", file=sys.stderr)
                                    continue
                                if agent and not skill.is_compatible_with_agent(agent):
                                    print(f"[SEARCH DEBUG] Filtered by agent compatibility", file=sys.stderr)
                                    continue
                                if tags and not any(tag in skill.tags for tag in tags):
                                    print(f"[SEARCH DEBUG] Filtered by tags - no match", file=sys.stderr)
                                    continue

                                # Text query
                                if query:
                                    query_lower = query.lower()
                                    text_fields = [
                                        skill.name.lower(),
                                        skill.description.lower(),
                                        *[tag.lower() for tag in skill.tags],
                                    ]
                                    if not any(query_lower in field for field in text_fields):
                                        continue

                                print(f"[SEARCH DEBUG] Skill {skill.skill_id} passed all filters!", file=sys.stderr)
                                results.append(skill)
                                seen_skill_ids.add(skill.skill_id)

                                if len(results) >= max_results:
                                    return results

                            except Exception as e:
                                print(f"Warning: Failed to load {skill_file}: {e}")
                                continue

            # Method 2: Direct .yaml files in search_path
            for skill_file in search_path.glob("*.yaml"):
                if skill_file.is_file():
                    try:
                        skill = self._load_from_file(skill_file)

                        if skill.skill_id in seen_skill_ids:
                            continue

                        # Apply same filters
                        if status and skill.status != status:
                            continue
                        if visibility and skill.visibility != visibility:
                            continue
                        if agent and not skill.is_compatible_with_agent(agent):
                            continue
                        if tags and not any(tag in skill.tags for tag in tags):
                            continue
                        if query:
                            query_lower = query.lower()
                            text_fields = [
                                skill.name.lower(),
                                skill.description.lower(),
                                *[tag.lower() for tag in skill.tags],
                            ]
                            if not any(query_lower in field for field in text_fields):
                                continue

                        results.append(skill)
                        seen_skill_ids.add(skill.skill_id)

                        if len(results) >= max_results:
                            return results

                    except Exception as e:
                        print(f"Warning: Failed to load {skill_file}: {e}")
                        continue

            # Method 3: Versioned structure - skill_id/version/skill.yaml
            for skill_dir in search_path.iterdir():
                if not skill_dir.is_dir():
                    continue

                # Skip agent subdirectories (already handled above)
                if skill_dir.name in ["director", "cinematographer", "editor", "skills_manager"]:
                    continue

                # Get latest version
                versions = sorted(
                    [v.name for v in skill_dir.iterdir() if v.is_dir()],
                    reverse=True
                )
                if not versions:
                    continue

                skill_path = skill_dir / versions[0] / "skill.yaml"
                if not skill_path.exists():
                    continue

                try:
                    skill = self._load_from_file(skill_path)

                    if skill.skill_id in seen_skill_ids:
                        continue

                    # Apply filters
                    if status and skill.status != status:
                        continue
                    if visibility and skill.visibility != visibility:
                        continue
                    if agent and not skill.is_compatible_with_agent(agent):
                        continue
                    if tags and not any(tag in skill.tags for tag in tags):
                        continue
                    if query:
                        query_lower = query.lower()
                        text_fields = [
                            skill.name.lower(),
                            skill.description.lower(),
                            *[tag.lower() for tag in skill.tags],
                        ]
                        if not any(query_lower in field for field in text_fields):
                            continue

                    results.append(skill)
                    seen_skill_ids.add(skill.skill_id)

                    if len(results) >= max_results:
                        return results

                except Exception as e:
                    print(f"Warning: Failed to load {skill_path}: {e}")
                    continue

        return results

    def list_all(self) -> List[SkillManifest]:
        """List all available skills"""
        return self.search(max_results=1000)

    def delete_skill(self, skill_id: str, version: Optional[str] = None):
        """
        Delete a skill

        Args:
            skill_id: Skill identifier
            version: Specific version (None for all versions)
        """
        for search_path in [
            self.community_path,
            self.personal_path,
            self.pending_path,
            self.deprecated_path,
        ]:
            skill_path = search_path / skill_id
            if not skill_path.exists():
                continue

            if version:
                version_path = skill_path / version
                if version_path.exists():
                    import shutil
                    shutil.rmtree(version_path)
            else:
                import shutil
                shutil.rmtree(skill_path)

    def fork_skill(self, skill_id: str, new_author_id: str) -> SkillManifest:
        """
        Fork a skill for personal modification

        Args:
            skill_id: Original skill ID
            new_author_id: New author identifier

        Returns:
            Forked skill manifest
        """
        # Load original
        original = self.load_skill(skill_id)
        if not original:
            raise ValueError(f"Skill {skill_id} not found")

        # Create fork
        fork_data = original.model_dump()
        fork_data["skill_id"] = f"{skill_id}_fork_{new_author_id}"
        fork_data["version"] = "0.1.0"
        fork_data["parent_skill"] = f"{skill_id}@{original.version}"
        fork_data["status"] = SkillStatus.DRAFT
        fork_data["visibility"] = SkillVisibility.LOCAL
        fork_data["author"]["id"] = new_author_id
        fork_data["created_at"] = datetime.utcnow().isoformat()
        fork_data["updated_at"] = fork_data["created_at"]

        fork = SkillManifest(**fork_data)

        # Save to personal
        self.save_skill(fork, location="personal")

        return fork
