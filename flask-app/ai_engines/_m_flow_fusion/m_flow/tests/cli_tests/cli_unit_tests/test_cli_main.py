"""
CLI主入口测试
"""

from __future__ import annotations

import argparse

import pytest
from unittest.mock import MagicMock, patch

from m_flow.cli.app import _build_parser as _create_parser, _load_commands as _discover_commands, main
from m_flow.cli.exceptions import CliCommandException


class TestCommandDiscovery:
    """命令发现测试"""

    def test_discover_returns_commands(self):
        """测试命令发现返回命令列表"""
        cmds = _discover_commands()
        assert len(cmds) > 0
        strs = [c().command_string for c in cmds]
        for exp in ("add", "search", "memorize", "delete", "config"):
            assert exp in strs

    def test_parser_creation(self):
        """测试解析器创建"""
        parser, installed = _create_parser()
        assert isinstance(parser, argparse.ArgumentParser)
        for exp in ("add", "search", "memorize", "delete", "config"):
            assert exp in installed
        dests = [a.dest for a in parser._actions]
        assert "version" in dests


class TestMainFunction:
    """main函数测试"""

    @patch("m_flow.cli.app._build_parser")
    def test_no_cmd_prints_help(self, mock_cp):
        """测试无命令时打印帮助"""
        p = MagicMock()
        p.parse_args.return_value = MagicMock(command=None, spec={})
        mock_cp.return_value = (p, {})
        assert main() == -1
        p.print_help.assert_called_once()

    @patch("m_flow.cli.app._build_parser")
    def test_valid_cmd_executes(self, mock_cp):
        """测试有效命令执行"""
        cmd = MagicMock()
        cmd.execute.return_value = None
        p = MagicMock()
        args = MagicMock(command="x", spec={})
        p.parse_args.return_value = args
        mock_cp.return_value = (p, {"x": cmd})
        assert main() == 0
        cmd.execute.assert_called_once_with(args)

    @patch("m_flow.cli.app._build_parser")
    @patch("m_flow.cli.debug.is_debug_enabled")
    def test_cmd_exception(self, mock_dbg, mock_cp):
        """测试命令异常返回错误码"""
        mock_dbg.return_value = False
        cmd = MagicMock()
        cmd.execute.side_effect = CliCommandException("err", error_code=2)
        p = MagicMock()
        p.parse_args.return_value = MagicMock(command="x", spec={})
        mock_cp.return_value = (p, {"x": cmd})
        assert main() == 2

    @patch("m_flow.cli.app._build_parser")
    @patch("m_flow.cli.debug.is_debug_enabled")
    def test_generic_exception(self, mock_dbg, mock_cp):
        """测试通用异常返回-1"""
        mock_dbg.return_value = False
        cmd = MagicMock()
        cmd.execute.side_effect = Exception("err")
        p = MagicMock()
        p.parse_args.return_value = MagicMock(command="x", spec={})
        mock_cp.return_value = (p, {"x": cmd})
        assert main() == -1

    @patch("m_flow.cli.app._build_parser")
    @patch("m_flow.cli.debug.is_debug_enabled")
    def test_debug_reraises(self, mock_dbg, mock_cp):
        """测试调试模式重新抛出异常"""
        mock_dbg.return_value = True
        exc = CliCommandException("err", error_code=2, cause=ValueError("inner"))
        cmd = MagicMock()
        cmd.execute.side_effect = exc
        p = MagicMock()
        p.parse_args.return_value = MagicMock(command="x", spec={})
        mock_cp.return_value = (p, {"x": cmd})
        with pytest.raises(ValueError, match="inner"):
            main()


class TestParserArgs:
    """解析器参数测试"""

    def test_version_arg(self):
        """测试版本参数"""
        p, _ = _create_parser()
        acts = [a for a in p._actions if a.dest == "version"]
        assert len(acts) == 1
        assert "m_flow" in acts[0].version

    def test_debug_arg(self):
        """测试调试参数（--debug 使用 SUPPRESS 作为 dest，需按 action 类型或选项字符串查找）"""
        from m_flow.cli.app import _ToggleDebug

        p, _ = _create_parser()
        acts = [a for a in p._actions if isinstance(a, _ToggleDebug)]
        assert len(acts) == 1
        assert "--debug" in acts[0].option_strings


class TestDebugAction:
    """调试动作测试"""

    @patch("m_flow.cli.debug.enable_debug")
    @patch("m_flow.cli.echo.note")
    def test_action_call(self, mock_note, mock_enable):
        """测试调试动作启用调试模式"""
        from m_flow.cli.app import _ToggleDebug as DebugAction

        act = DebugAction([])
        act(MagicMock(), MagicMock(), None)
        mock_enable.assert_called_once()
        mock_note.assert_called_once()
