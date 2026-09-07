from pathlib import Path

from pydantic_ai import Agent

from app.tools.repo_read import (
    grep_repo,
    list_repo_tree,
    read_repo_file,
    search_repo_files,
)


def register_code_tools(
    agent: Agent,
    repo_root: Path,
    allowed_extensions: frozenset[str],
) -> None:
    @agent.tool_plain(
        name="list_repo_tree",
        description="列出代码仓库的文件目录树。用于了解项目结构，找到可能相关的文件。",
    )
    def _list_tree() -> str:
        return list_repo_tree(repo_root, allowed_extensions)

    @agent.tool_plain(
        name="read_repo_file",
        description=(
            "读取仓库中指定文件的完整内容。"
            "参数 relative_path 是相对于仓库根目录的路径，例如 'app/main.py'。"
        ),
    )
    def _read_file(relative_path: str) -> str:
        return read_repo_file(repo_root, relative_path, allowed_extensions)

    @agent.tool_plain(
        name="search_repo_files",
        description=(
            "按文件名模糊搜索仓库中的文件。"
            "参数 pattern 是文件路径的子串，例如 'config' 或 'layout.liquid'。"
        ),
    )
    def _search_files(pattern: str) -> str:
        return search_repo_files(repo_root, pattern, allowed_extensions)

    @agent.tool_plain(
        name="grep_repo",
        description=(
            "在仓库文件内容中搜索包含指定文本的行。"
            "参数 query 是要搜索的字符串，例如函数名、变量名或错误信息。"
        ),
    )
    def _grep(query: str) -> str:
        return grep_repo(repo_root, query, allowed_extensions)
