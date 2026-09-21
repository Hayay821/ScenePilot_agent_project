"""
Editor Agent

Creates post-production timeline and edit plans.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from .base_agent import BaseAgent
from ..schemas import (
    AgentType,
    AgentResult,
    EditPlan,
    TimelineSegment,
    PanoramaTrack,
    RenderConfig,
    Event,
)


class EditorAgent(BaseAgent):
    """
    Editor Agent

    Responsibilities:
    1. Analyze events and media evidence
    2. Create timeline with segments
    3. Generate panorama reframe tracks
    4. Plan subtitles and effects
    5. Output edit plan for rendering
    """

    def __init__(self, model_provider: Optional[Any] = None):
        super().__init__(AgentType.EDITOR, model_provider)

    def process(self, context: Dict[str, Any]) -> AgentResult:
        """
        Process events and media to create edit plan

        Context keys:
        - plan: DirectorPlan
        - events: List of detected events
        - media_sources: Available media sources
        - intent: NormalizedIntent
        - session_id: Session identifier
        """
        plan = context.get("plan")
        events = context.get("events", [])
        media_sources = context.get("media_sources", [])
        intent = context.get("intent")
        session_id = context.get("session_id", "session_unknown")

        if not plan or not intent:
            raise ValueError("DirectorPlan and Intent are required")

        # Use model provider or mock
        if self.model_provider:
            from ..schemas import EditPlan as EditPlanSchema
            response = self.model_provider.generate(
                prompt=self._build_prompt(plan, events, media_sources, intent),
                schema=EditPlanSchema,
            )
        else:
            # Fallback: rule-based edit plan
            response = self._create_rule_based_edit_plan(
                plan, events, media_sources, intent, session_id
            )

        # Create EditPlan
        edit_plan = EditPlan(**response)

        # Create result
        result = self._create_result(
            session_id=session_id,
            intent_id=intent.get("intent_id") if isinstance(intent, dict) else intent.intent_id,
            output=edit_plan,
            confidence=edit_plan.confidence,
        )

        # Add teaching notes
        if edit_plan.explanations:
            result.teaching_notes = edit_plan.explanations

        return result

    def _build_prompt(
        self,
        plan: Any,
        events: List[Any],
        media_sources: List[Any],
        intent: Any
    ) -> str:
        """Build prompt for LLM"""
        prompt = f"""
作为剪辑AI，根据导演计划和检测到的事件创建剪辑方案。

导演计划: {plan}
检测事件: {events}
可用素材: {media_sources}
用户意图: {intent}

请输出:
1. 时间线段落（选择关键片段）
2. 全景重构轨迹（如适用）
3. 字幕规划
4. 渲染配置
5. 剪辑决策说明
"""
        return prompt

    def _create_rule_based_edit_plan(
        self,
        plan: Any,
        events: List[Any],
        media_sources: List[Any],
        intent: Any,
        session_id: str
    ) -> Dict[str, Any]:
        """Create edit plan based on plan and events"""
        edit_plan_id = f"edit_{uuid.uuid4().hex[:8]}"

        # Extract data
        if isinstance(plan, dict):
            plan_id = plan.get("plan_id", "unknown")
            shot_intentions = plan.get("shot_intentions", [])
        else:
            plan_id = plan.plan_id
            shot_intentions = [s.model_dump() for s in plan.shot_intentions]

        if isinstance(intent, dict):
            intent_id = intent.get("intent_id", "unknown")
            output_req = intent.get("output", {})
        else:
            intent_id = intent.intent_id
            output_req = intent.output.model_dump()

        # Create timeline segments based on shot intentions
        timeline = []
        current_time = 0

        for idx, intention in enumerate(shot_intentions):
            duration_ms = int((intention.get("duration_hint_sec", 5.0)) * 1000)
            camera = intention.get("camera", "x4air")
            stage = intention.get("stage", f"segment_{idx}")

            segment = {
                "source_id": f"{camera}_{idx:03d}",
                "start_ms": current_time,
                "end_ms": current_time + duration_ms,
                "role": stage,
                "reason": intention.get("notes", f"拍摄{stage}阶段"),
                "confidence": 0.85,
                "speed": 1.0,
                "volume": 1.0,
                "effects": []
            }
            timeline.append(segment)
            current_time += duration_ms

        # Match events to timeline segments
        for event in events:
            if isinstance(event, dict):
                event_type = event.get("event_type")
                event_start = event.get("start_ms", 0)
            elif hasattr(event, "event_type"):
                event_type = event.event_type.value if hasattr(event.event_type, "value") else event.event_type
                event_start = event.start_ms
            else:
                continue

            # Find matching segment
            for segment in timeline:
                if segment["start_ms"] <= event_start < segment["end_ms"]:
                    segment["confidence"] = min(1.0, segment["confidence"] + 0.05)
                    break

        # Panorama tracks (if applicable)
        panorama_tracks = []
        # Simple example: static center track
        if any(s.get("camera") == "x4air" for s in shot_intentions):
            panorama_tracks.append({
                "time_ms": 0,
                "yaw": 0.0,
                "pitch": 0.0,
                "fov": 90.0,
                "easing": "linear"
            })

        # Render config
        render = {
            "ratio": output_req.get("ratio", "16:9"),
            "resolution": "1920x1080",
            "fps": 30,
            "codec": "h264",
            "quality": output_req.get("quality", "high")
        }

        # Calculate total duration
        total_duration_ms = timeline[-1]["end_ms"] if timeline else 0

        # Explanations
        explanations = [
            f"根据导演计划创建{len(timeline)}段剪辑",
            "保留完整叙事弧线，包括准备、高潮和反应",
        ]

        if events:
            explanations.append(f"匹配了{len(events)}个检测到的事件")

        return {
            "edit_plan_id": edit_plan_id,
            "session_id": session_id,
            "intent_id": intent_id,
            "timeline": timeline,
            "panorama_tracks": panorama_tracks,
            "subtitles": [],
            "render": render,
            "total_duration_ms": total_duration_ms,
            "source_count": len(timeline),
            "explanations": explanations,
            "warnings": [],
            "plan_id": plan_id,
            "skill_bundle_id": plan.get("skill_bundle_id") if isinstance(plan, dict) else plan.skill_bundle_id,
            "created_at": datetime.utcnow().isoformat(),
            "confidence": 0.80,
        }
