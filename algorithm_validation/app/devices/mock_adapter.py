"""
Mock 设备适配器
用于无硬件时记录命令
"""

from typing import List
from pathlib import Path
import json
from loguru import logger

from app.core.schemas import CameraAction
from app.core.settings import settings


class MockDeviceAdapter:
    """
    Mock 设备适配器
    不执行真实命令，只记录到文件
    """

    def __init__(self, output_dir: Path):
        """
        Args:
            output_dir: 命令记录输出目录
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.commands_file = output_dir / "commands.jsonl"
        self.commands = []

        logger.info(f"MockDeviceAdapter initialized: {self.commands_file}")

    def execute(self, action: CameraAction) -> dict:
        """
        执行命令（Mock模式：只记录）

        Args:
            action: 设备命令

        Returns:
            执行结果
        """
        # 记录命令
        command_record = {
            "action_id": action.action_id,
            "action_type": action.action_type,
            "timestamp_ms": action.timestamp_ms,
            "params": action.params,
            "status": "mocked",
        }

        self.commands.append(command_record)

        # 追加写入 JSONL
        with open(self.commands_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(command_record, ensure_ascii=False) + "\n")

        logger.debug(
            f"Mock executed: {action.action_type} at {action.timestamp_ms}ms"
        )

        return {
            "success": True,
            "message": f"Mocked {action.action_type}",
        }

    def execute_batch(self, actions: List[CameraAction]) -> List[dict]:
        """批量执行命令"""
        results = []
        for action in actions:
            result = self.execute(action)
            results.append(result)
        return results

    def get_commands(self) -> List[dict]:
        """获取所有已记录的命令"""
        return self.commands

    def get_stats(self) -> dict:
        """获取统计信息"""
        if not self.commands:
            return {
                "total_commands": 0,
                "command_types": {},
            }

        # 统计命令类型
        type_counts = {}
        for cmd in self.commands:
            action_type = cmd["action_type"]
            type_counts[action_type] = type_counts.get(action_type, 0) + 1

        return {
            "total_commands": len(self.commands),
            "command_types": type_counts,
            "first_command_ms": self.commands[0]["timestamp_ms"],
            "last_command_ms": self.commands[-1]["timestamp_ms"],
        }

    def reset(self):
        """重置（清空命令记录）"""
        self.commands = []
        if self.commands_file.exists():
            self.commands_file.unlink()
        logger.info("MockDeviceAdapter reset")
