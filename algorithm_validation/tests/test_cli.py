"""
CLI 测试
"""

import pytest
from pathlib import Path
from click.testing import CliRunner

from app.cli import cli, analyze_video


class TestCLI:
    """测试 CLI"""

    def test_cli_help(self):
        """测试帮助命令"""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "ScenePilot" in result.output

    def test_analyze_help(self):
        """测试 analyze 命令帮助"""
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", "--help"])
        assert result.exit_code == 0
        assert "分析视频" in result.output

    def test_stats_help(self):
        """测试 stats 命令帮助"""
        runner = CliRunner()
        result = runner.invoke(cli, ["stats", "--help"])
        assert result.exit_code == 0
        assert "事件统计" in result.output
