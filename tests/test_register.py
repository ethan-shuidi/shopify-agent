from pathlib import Path

from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from app.tools.register import register_code_tools

EXTS = frozenset({".py", ".js"})


def test_registers_four_tools(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("x = 1")
    agent = Agent(TestModel())
    register_code_tools(agent, tmp_path, EXTS)

    tool_names = set(agent._function_toolset.tools.keys())
    assert tool_names == {"list_repo_tree", "read_repo_file", "search_repo_files", "grep_repo"}
