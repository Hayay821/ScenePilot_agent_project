"""
导演状态机测试
"""

import pytest
from app.director import DirectorStateMachine, DirectorState, DirectorContext
from app.core.schemas import VideoEvent


class TestDirectorStateMachine:
    """测试导演状态机"""

    def test_state_machine_init(self):
        """测试初始化"""
        sm = DirectorStateMachine(
            idle_timeout_ms=5000,
            search_timeout_ms=10000,
            recover_timeout_ms=15000,
        )
        assert sm.idle_timeout_ms == 5000
        assert sm.search_timeout_ms == 10000
        assert sm.recover_timeout_ms == 15000

    def test_initial_context(self):
        """测试初始上下文"""
        sm = DirectorStateMachine()
        context = sm.create_initial_context()

        assert context.current_state == DirectorState.IDLE
        assert context.current_subject is None
        assert context.recording is False
        assert context.last_event_timestamp == 0
        assert len(context.highlight_segments) == 0

    def test_idle_to_track_on_subject_entry(self):
        """测试：主体进入时从 IDLE → TRACK"""
        sm = DirectorStateMachine()
        context = sm.create_initial_context()

        # 创建主体进入事件
        event = VideoEvent(
            event_id="evt_001",
            start_ms=1000,
            end_ms=2000,
            event_type="subject_entry",
            description="主体进入画面",
            confidence=0.9,
            highlight_score=0.6,
            key_subjects=["subject_1"],
            camera_suggestion="track",
        )

        actions, new_context = sm.process_events([event], context, 2000)

        assert new_context.current_state == DirectorState.TRACK
        assert new_context.current_subject == "subject_1"
        assert len(actions) == 1
        assert actions[0].action_type == "start_tracking"

    def test_idle_to_search_on_action_peak(self):
        """测试：检测到动作但无主体时从 IDLE → SEARCH"""
        sm = DirectorStateMachine()
        context = sm.create_initial_context()

        event = VideoEvent(
            event_id="evt_001",
            start_ms=1000,
            end_ms=2000,
            event_type="action_peak",
            description="动作高潮",
            confidence=0.9,
            highlight_score=0.8,
            key_subjects=[],
            camera_suggestion="track",
        )

        actions, new_context = sm.process_events([event], context, 2000)

        assert new_context.current_state == DirectorState.SEARCH
        assert len(actions) == 1
        assert actions[0].action_type == "search_subject"

    def test_track_to_record_on_high_action_peak(self):
        """测试：高光动作时从 TRACK → RECORD"""
        sm = DirectorStateMachine()
        context = DirectorContext(
            current_state=DirectorState.TRACK,
            current_subject="subject_1",
            recording=False,
            last_event_timestamp=0,
            last_transition_timestamp=0,
            highlight_segments=[],
            idle_duration_ms=0,
        )

        event = VideoEvent(
            event_id="evt_001",
            start_ms=1000,
            end_ms=2000,
            event_type="action_peak",
            description="动作高潮",
            confidence=0.95,
            highlight_score=0.85,  # 高于 0.7 阈值
            key_subjects=["subject_1"],
            camera_suggestion="track",
        )

        actions, new_context = sm.process_events([event], context, 2000)

        assert new_context.current_state == DirectorState.RECORD
        assert new_context.recording is True
        assert len(actions) == 1
        assert actions[0].action_type == "start_recording"

    def test_record_to_highlight_on_super_peak(self):
        """测试：超高光时刻从 RECORD → HIGHLIGHT"""
        sm = DirectorStateMachine()
        context = DirectorContext(
            current_state=DirectorState.RECORD,
            current_subject="subject_1",
            recording=True,
            last_event_timestamp=1000,
            last_transition_timestamp=1000,
            highlight_segments=[],
            idle_duration_ms=0,
        )

        event = VideoEvent(
            event_id="evt_001",
            start_ms=2000,
            end_ms=3000,
            event_type="action_peak",
            description="超级高潮",
            confidence=0.98,
            highlight_score=0.92,  # 高于 0.8 阈值
            key_subjects=["subject_1"],
            camera_suggestion="zoom",
        )

        actions, new_context = sm.process_events([event], context, 3000)

        assert new_context.current_state == DirectorState.HIGHLIGHT
        assert len(new_context.highlight_segments) == 1
        assert new_context.highlight_segments[0] == (2000, 3000)
        assert len(actions) == 1
        assert actions[0].action_type == "mark_highlight"

    def test_track_to_recover_on_subject_exit(self):
        """测试：主体离开时从 TRACK → RECOVER"""
        sm = DirectorStateMachine()
        context = DirectorContext(
            current_state=DirectorState.TRACK,
            current_subject="subject_1",
            recording=False,
            last_event_timestamp=1000,
            last_transition_timestamp=1000,
            highlight_segments=[],
            idle_duration_ms=0,
        )

        event = VideoEvent(
            event_id="evt_001",
            start_ms=2000,
            end_ms=3000,
            event_type="subject_exit",
            description="主体离开",
            confidence=0.9,
            highlight_score=0.3,
            key_subjects=["subject_1"],
            camera_suggestion="observe",
        )

        actions, new_context = sm.process_events([event], context, 3000)

        assert new_context.current_state == DirectorState.RECOVER
        assert len(actions) == 1
        assert actions[0].action_type == "subject_lost"

    def test_recover_to_track_on_subject_reentry(self):
        """测试：主体重新进入时从 RECOVER → TRACK"""
        sm = DirectorStateMachine()
        context = DirectorContext(
            current_state=DirectorState.RECOVER,
            current_subject=None,
            recording=False,
            last_event_timestamp=2000,
            last_transition_timestamp=2000,
            highlight_segments=[],
            idle_duration_ms=0,
        )

        event = VideoEvent(
            event_id="evt_001",
            start_ms=3000,
            end_ms=4000,
            event_type="subject_entry",
            description="主体重新进入",
            confidence=0.9,
            highlight_score=0.6,
            key_subjects=["subject_1"],
            camera_suggestion="track",
        )

        actions, new_context = sm.process_events([event], context, 4000)

        assert new_context.current_state == DirectorState.TRACK
        assert new_context.current_subject == "subject_1"
        assert len(actions) == 1
        assert actions[0].action_type == "resume_tracking"

    def test_search_timeout(self):
        """测试：搜索超时"""
        sm = DirectorStateMachine(search_timeout_ms=5000)
        context = DirectorContext(
            current_state=DirectorState.SEARCH,
            current_subject=None,
            recording=False,
            last_event_timestamp=0,
            last_transition_timestamp=0,
            highlight_segments=[],
            idle_duration_ms=0,
        )

        # 6秒后仍无事件 → 超时
        actions, new_context = sm.process_events([], context, 6000)

        assert new_context.current_state == DirectorState.IDLE
        assert len(actions) == 1
        assert actions[0].action_type == "search_timeout"

    def test_recover_timeout(self):
        """测试：恢复超时"""
        sm = DirectorStateMachine(recover_timeout_ms=10000)
        context = DirectorContext(
            current_state=DirectorState.RECOVER,
            current_subject="subject_1",
            recording=False,
            last_event_timestamp=0,
            last_transition_timestamp=0,
            highlight_segments=[],
            idle_duration_ms=0,
        )

        # 11秒后仍未恢复 → 超时
        actions, new_context = sm.process_events([], context, 11000)

        assert new_context.current_state == DirectorState.IDLE
        assert new_context.current_subject is None
        assert len(actions) == 1
        assert actions[0].action_type == "recover_timeout"

    def test_max_recording_time(self):
        """测试：最大录制时长限制"""
        sm = DirectorStateMachine()
        context = DirectorContext(
            current_state=DirectorState.RECORD,
            current_subject="subject_1",
            recording=True,
            last_event_timestamp=0,
            last_transition_timestamp=0,
            highlight_segments=[],
            idle_duration_ms=0,
        )

        # 31秒后仍在录制 → 强制停止
        actions, new_context = sm.process_events([], context, 31000)

        assert new_context.current_state == DirectorState.TRACK
        assert new_context.recording is False
        assert len(actions) == 1
        assert actions[0].action_type == "max_recording_time"

    def test_multiple_events_processing(self):
        """测试：处理多个事件"""
        sm = DirectorStateMachine()
        context = sm.create_initial_context()

        events = [
            VideoEvent(
                event_id="evt_001",
                start_ms=1000,
                end_ms=2000,
                event_type="subject_entry",
                description="主体进入",
                confidence=0.9,
                highlight_score=0.6,
                key_subjects=["subject_1"],
                camera_suggestion="track",
            ),
            VideoEvent(
                event_id="evt_002",
                start_ms=3000,
                end_ms=4000,
                event_type="action_peak",
                description="动作高潮",
                confidence=0.95,
                highlight_score=0.85,
                key_subjects=["subject_1"],
                camera_suggestion="zoom",
            ),
        ]

        actions, new_context = sm.process_events(events, context, 4000)

        # 应该有两个状态转换：IDLE → TRACK → RECORD
        assert new_context.current_state == DirectorState.RECORD
        assert new_context.recording is True
        assert len(actions) == 2  # start_tracking + start_recording


class TestMockDeviceAdapter:
    """测试 Mock 设备适配器"""

    def test_mock_adapter_execute(self, tmp_path):
        """测试执行命令"""
        from app.devices import MockDeviceAdapter
        from app.core.schemas import CameraAction

        adapter = MockDeviceAdapter(tmp_path)

        action = CameraAction(
            action_id="action_001",
            action_type="start_tracking",
            timestamp_ms=1000,
            params={"subject_id": "subject_1"},
        )

        result = adapter.execute(action)

        assert result["success"] is True
        assert len(adapter.commands) == 1
        assert adapter.commands[0]["action_type"] == "start_tracking"

    def test_mock_adapter_batch_execute(self, tmp_path):
        """测试批量执行"""
        from app.devices import MockDeviceAdapter
        from app.core.schemas import CameraAction

        adapter = MockDeviceAdapter(tmp_path)

        actions = [
            CameraAction(
                action_id=f"action_{i:03d}",
                action_type="track",
                timestamp_ms=i * 1000,
                params={},
            )
            for i in range(5)
        ]

        results = adapter.execute_batch(actions)

        assert len(results) == 5
        assert all(r["success"] for r in results)
        assert len(adapter.commands) == 5

    def test_mock_adapter_stats(self, tmp_path):
        """测试统计信息"""
        from app.devices import MockDeviceAdapter
        from app.core.schemas import CameraAction

        adapter = MockDeviceAdapter(tmp_path)

        # 执行不同类型的命令
        actions = [
            CameraAction(action_id="a1", action_type="start_tracking", timestamp_ms=1000, params={}),
            CameraAction(action_id="a2", action_type="start_recording", timestamp_ms=2000, params={}),
            CameraAction(action_id="a3", action_type="start_tracking", timestamp_ms=3000, params={}),
        ]

        adapter.execute_batch(actions)
        stats = adapter.get_stats()

        assert stats["total_commands"] == 3
        assert stats["command_types"]["start_tracking"] == 2
        assert stats["command_types"]["start_recording"] == 1
        assert stats["first_command_ms"] == 1000
        assert stats["last_command_ms"] == 3000
