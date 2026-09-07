from app.prompts import build_system_prompt


def test_no_tools_prompt_has_disclaimer() -> None:
    prompt = build_system_prompt(code_repo_enabled=False)
    assert "没有" in prompt
    assert "文件系统" in prompt or "工具" in prompt


def test_code_tools_prompt_has_tool_instructions() -> None:
    prompt = build_system_prompt(code_repo_enabled=True)
    assert "list_repo_tree" in prompt
    assert "read_repo_file" in prompt
    assert "search_repo_files" in prompt
    assert "grep_repo" in prompt


def test_code_tools_prompt_removes_no_tools_disclaimer() -> None:
    prompt = build_system_prompt(code_repo_enabled=True)
    assert "没有 Shopify、文件系统" not in prompt


def test_both_prompts_share_base() -> None:
    no_tools = build_system_prompt(code_repo_enabled=False)
    with_tools = build_system_prompt(code_repo_enabled=True)
    assert "飞书" in no_tools
    assert "飞书" in with_tools
    assert "不要泄露" in no_tools
    assert "不要泄露" in with_tools
