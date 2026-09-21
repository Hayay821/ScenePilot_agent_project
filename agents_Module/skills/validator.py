"""
Skill Validator

Validates skill manifests for safety and correctness.
"""

from typing import List, Dict, Any, Set
from ..schemas import SkillManifest, SkillStatus


class SkillValidator:
    """
    Skill validation and safety checking

    Ensures skills follow safety constraints and schema requirements.
    """

    # Whitelist of allowed actions
    ALLOWED_ACTIONS = {
        # Suggestions only (no direct execution)
        "suggest_composition",
        "suggest_tracking",
        "suggest_reframe",
        "mark_highlight",
        "set_priority",

        # Safe device suggestions
        "suggest_pan_tilt",
        "suggest_zoom",
        "suggest_focus",

        # Recording control (requires validation)
        "suggest_start_recording",
        "suggest_stop_recording",

        # Timeline editing
        "mark_segment",
        "set_duration",
        "add_subtitle",
    }

    # Forbidden actions (must never appear)
    FORBIDDEN_ACTIONS = {
        # Direct device control
        "execute_command",
        "control_device",
        "send_command",

        # Destructive operations
        "delete_media",
        "format_storage",
        "erase_card",
        "factory_reset",
        "firmware_upgrade",

        # System operations
        "execute_shell",
        "run_script",
        "eval_code",
        "import_module",

        # Network operations
        "upload_file",
        "download_file",
        "send_request",
        "open_socket",
    }

    # Actions requiring human approval
    APPROVAL_REQUIRED = {
        "publish",
        "upload",
        "share",
        "overwrite_skill",
        "delete_skill",
    }

    def __init__(self):
        pass

    def validate(self, skill: SkillManifest) -> tuple[bool, List[str]]:
        """
        Validate skill manifest

        Args:
            skill: Skill to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Schema validation (already done by Pydantic)
        # Additional business logic validation

        # 1. Check actions whitelist
        action_errors = self._validate_actions(skill)
        errors.extend(action_errors)

        # 2. Check safety configuration
        safety_errors = self._validate_safety(skill)
        errors.extend(safety_errors)

        # 3. Check status transitions
        status_errors = self._validate_status(skill)
        errors.extend(status_errors)

        # 4. Check agent bindings
        binding_errors = self._validate_agent_bindings(skill)
        errors.extend(binding_errors)

        # 5. Check version format
        version_errors = self._validate_version(skill)
        errors.extend(version_errors)

        return len(errors) == 0, errors

    def _validate_actions(self, skill: SkillManifest) -> List[str]:
        """Validate action whitelist"""
        errors = []

        # Check allowed actions
        for action in skill.safety.allowed_actions:
            if action not in self.ALLOWED_ACTIONS:
                errors.append(f"Unknown action in allowed list: {action}")

        # Check for forbidden actions
        forbidden_found = set(skill.safety.allowed_actions) & self.FORBIDDEN_ACTIONS
        if forbidden_found:
            errors.append(f"Forbidden actions found: {forbidden_found}")

        # Check rules for forbidden patterns
        for rule in skill.rules:
            advice_dict = rule.advice.model_dump(exclude_none=True)
            for key, value in advice_dict.items():
                if isinstance(value, str):
                    # Check for shell commands or code execution patterns
                    dangerous_patterns = [
                        "exec", "eval", "shell", "system",
                        "rm -rf", "format", "delete",
                    ]
                    for pattern in dangerous_patterns:
                        if pattern in value.lower():
                            errors.append(
                                f"Dangerous pattern '{pattern}' found in rule {rule.id}"
                            )

        return errors

    def _validate_safety(self, skill: SkillManifest) -> List[str]:
        """Validate safety configuration"""
        errors = []

        # Check minimum confidence
        if skill.safety.min_confidence_for_device_suggestion < 0.5:
            errors.append(
                "min_confidence_for_device_suggestion must be >= 0.5"
            )

        # Check approval requirements
        for action in skill.safety.requires_human_approval:
            if action not in self.APPROVAL_REQUIRED and action not in self.ALLOWED_ACTIONS:
                errors.append(
                    f"Unknown action in requires_human_approval: {action}"
                )

        return errors

    def _validate_status(self, skill: SkillManifest) -> List[str]:
        """Validate status and visibility"""
        errors = []

        # Published skills must have proper metadata
        if skill.status == SkillStatus.PUBLISHED:
            if not skill.author.verified:
                errors.append("Published skills require verified author")

            if skill.visibility.value == "local":
                errors.append("Published skills cannot be local-only")

            if not skill.license:
                errors.append("Published skills require license")

        return errors

    def _validate_agent_bindings(self, skill: SkillManifest) -> List[str]:
        """Validate agent bindings"""
        errors = []

        # At least one agent must be bound
        bindings = skill.agent_bindings
        if not any([
            bindings.director,
            bindings.cinematographer,
            bindings.editor,
            bindings.skills_manager,
        ]):
            errors.append("Skill must bind to at least one agent")

        return errors

    def _validate_version(self, skill: SkillManifest) -> List[str]:
        """Validate version format"""
        errors = []

        # Check semantic versioning
        version = skill.version
        parts = version.split(".")
        if len(parts) != 3:
            errors.append(f"Version must be semantic (major.minor.patch): {version}")
        else:
            try:
                [int(p) for p in parts]
            except ValueError:
                errors.append(f"Version parts must be integers: {version}")

        return errors

    def can_publish(self, skill: SkillManifest) -> tuple[bool, List[str]]:
        """
        Check if skill can be published to cloud

        Args:
            skill: Skill to check

        Returns:
            Tuple of (can_publish, reasons)
        """
        reasons = []

        # Must be in review status
        if skill.status != SkillStatus.REVIEW:
            reasons.append(f"Status must be 'review', got '{skill.status.value}'")

        # Must pass validation
        is_valid, errors = self.validate(skill)
        if not is_valid:
            reasons.extend(errors)

        # Must not be local-only
        if skill.visibility.value == "local":
            reasons.append("Cannot publish local-only skills")

        # Must have license
        if not skill.license:
            reasons.append("License is required for publication")

        # Check for sensitive data in examples
        if skill.evidence.examples:
            reasons.append(
                "Warning: Ensure example media has proper authorization and no PII"
            )

        return len(reasons) == 0, reasons

    def check_conflict(
        self,
        skill1: SkillManifest,
        skill2: SkillManifest
    ) -> tuple[bool, List[str]]:
        """
        Check if two skills have conflicting rules

        Args:
            skill1: First skill
            skill2: Second skill

        Returns:
            Tuple of (has_conflict, conflict_descriptions)
        """
        conflicts = []

        # Check for same event with different advice
        for rule1 in skill1.rules:
            for rule2 in skill2.rules:
                if rule1.when.event == rule2.when.event:
                    # Same event trigger
                    advice1 = rule1.advice.model_dump(exclude_none=True)
                    advice2 = rule2.advice.model_dump(exclude_none=True)

                    # Check for conflicting advice
                    for key in advice1:
                        if key in advice2 and advice1[key] != advice2[key]:
                            conflicts.append(
                                f"Conflict on event '{rule1.when.event}': "
                                f"{skill1.skill_id}.{rule1.id} suggests {key}={advice1[key]}, "
                                f"but {skill2.skill_id}.{rule2.id} suggests {key}={advice2[key]}"
                            )

        return len(conflicts) > 0, conflicts
