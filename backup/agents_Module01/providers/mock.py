"""
Mock Model Provider

Deterministic mock for testing without API calls.
"""

from typing import Dict, Any, Optional, List
import json


class MockProvider:
    """
    Mock model provider for testing

    Returns deterministic responses based on input.
    """

    def __init__(self):
        self.call_count = 0
        self.responses = []

    def generate(
        self,
        prompt: str,
        schema: Optional[type] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate mock response

        Args:
            prompt: Input prompt
            schema: Expected output schema
            **kwargs: Additional parameters

        Returns:
            Mock response dictionary
        """
        self.call_count += 1

        # Store call for testing
        self.responses.append({
            "prompt": prompt,
            "schema": schema.__name__ if schema else None,
            "kwargs": kwargs,
        })

        # Return deterministic response based on schema
        if schema:
            return self._generate_for_schema(schema, prompt)

        return {"response": "Mock response"}

    def _generate_for_schema(self, schema: type, prompt: str) -> Dict[str, Any]:
        """Generate mock data matching schema"""
        schema_name = schema.__name__

        # Different mock responses for different schemas
        if schema_name == "NormalizedIntent":
            return {
                "intent_id": f"intent_{self.call_count:03d}",
                "session_id": "session_test",
                "raw_input": "Mock user input",
                "goal": {
                    "goal_type": "action_story",
                    "subject": "single_person",
                    "priority": ["action_clarity", "peak_moment", "reaction"],
                    "style": "热血"
                },
                "output": {
                    "duration_sec": 30,
                    "ratio": "9:16",
                    "format": "mp4",
                    "quality": "high"
                },
                "skill_query": {
                    "tags": ["人像摄影", "导演计划"],
                    "agents": ["director", "cinematographer"],
                    "devices": ["link2", "x4air"],
                    "max_results": 3
                },
                "user_level": "beginner",
                "teaching_mode": True,
                "available_devices": ["link2", "x4air"],
                "device_preferences": {},
                "constraints": {},
                "created_at": "2026-09-22T00:00:00",
                "confidence": 0.85
            }

        elif schema_name == "DirectorPlan":
            return {
                "plan_id": f"plan_{self.call_count:03d}",
                "intent_id": "intent_001",
                "session_id": "session_test",
                "creative_goal": "突出动作成功和反应",
                "priorities": [
                    {"name": "action_peak", "weight": 1.0, "reason": "主要叙事节点"},
                    {"name": "reaction", "weight": 0.8, "reason": "情绪闭环"}
                ],
                "shot_intentions": [
                    {
                        "stage": "prepare",
                        "camera": "x4air",
                        "style": "wide_context",
                        "duration_hint_sec": 3.0,
                        "notes": "建立环境"
                    },
                    {
                        "stage": "peak",
                        "camera": "link2",
                        "style": "full_body_tracking",
                        "duration_hint_sec": 5.0,
                        "notes": "动作高潮"
                    }
                ],
                "conflicts": [],
                "decisions": [
                    {
                        "rule_id": "action_peak",
                        "skill_id": "action_coach",
                        "selected": True,
                        "reason": "最高优先级且设备支持"
                    }
                ],
                "teaching_notes": ["动作前保留环境有助于观众理解空间关系"],
                "requires_human_approval": False,
                "warnings": [],
                "skill_bundle_id": "bundle_001",
                "created_at": "2026-09-22T00:00:00",
                "confidence": 0.88
            }

        elif schema_name == "CinematographerRecommendation":
            return {
                "recommendation_id": f"rec_{self.call_count:03d}",
                "plan_id": "plan_001",
                "timestamp_ms": 5000,
                "state": "tracking",
                "subject": {
                    "id": "person_1",
                    "type": "person",
                    "bbox": [0.30, 0.20, 0.25, 0.65],
                    "confidence": 0.92,
                    "motion_vector": [0.1, 0.0],
                    "pose": "standing"
                },
                "shot_strategy": {
                    "composition": "full_body",
                    "camera_preference": "link2",
                    "tracking_speed": "normal",
                    "keep_pre_roll_ms": 3000,
                    "keep_post_roll_ms": None,
                    "frame_subject": True
                },
                "suggested_actions": [
                    {
                        "device": "link2",
                        "action": "set_composition",
                        "args": {"style": "full_body"},
                        "reason": "动作阶段需要展示身体运动",
                        "confidence": 0.88,
                        "priority": 90
                    }
                ],
                "current_stage": "peak",
                "active_rules": ["action_peak"],
                "explanation": "动作高潮阶段，使用全身构图突出主体动作",
                "requires_executor_validation": True,
                "warnings": [],
                "created_at": "2026-09-22T00:00:00",
                "confidence": 0.88
            }

        elif schema_name == "EditPlan":
            return {
                "edit_plan_id": f"edit_{self.call_count:03d}",
                "session_id": "session_test",
                "intent_id": "intent_001",
                "timeline": [
                    {
                        "source_id": "x4air_001",
                        "start_ms": 0,
                        "end_ms": 3000,
                        "role": "prepare",
                        "reason": "建立空间和动作前状态",
                        "confidence": 0.85,
                        "speed": 1.0,
                        "volume": 1.0,
                        "effects": []
                    },
                    {
                        "source_id": "link2_001",
                        "start_ms": 3000,
                        "end_ms": 8000,
                        "role": "peak",
                        "reason": "动作强度和主体清晰度最高",
                        "confidence": 0.92,
                        "speed": 1.0,
                        "volume": 1.0,
                        "effects": []
                    }
                ],
                "panorama_tracks": [],
                "subtitles": [],
                "render": {
                    "ratio": "9:16",
                    "resolution": "1920x1080",
                    "fps": 30,
                    "codec": "h264",
                    "quality": "high"
                },
                "total_duration_ms": 8000,
                "source_count": 2,
                "explanations": ["保留准备-高潮两段，形成完整叙事"],
                "warnings": [],
                "plan_id": "plan_001",
                "skill_bundle_id": "bundle_001",
                "created_at": "2026-09-22T00:00:00",
                "confidence": 0.87
            }

        # Default fallback
        return {"mock": True, "schema": schema_name}

    def reset(self):
        """Reset call count and responses"""
        self.call_count = 0
        self.responses = []
