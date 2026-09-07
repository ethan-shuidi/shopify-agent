from pathlib import Path

import pytest

from app.tools.repo_read import (
    grep_repo,
    list_repo_tree,
    read_repo_file,
    search_repo_files,
)

EXTS = frozenset({".py", ".js", ".json", ".md"})


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "main.py").write_text("print('hello')\n")
    (tmp_path / "app" / "utils.py").write_text("def add(a, b):\n    return a + b\n")
    (tmp_path / "package.json").write_text('{"name": "demo"}\n')
    (tmp_path / "README.md").write_text("# Demo\nThis is a demo project.\n")
    (tmp_path / "logo.png").write_bytes(b"\x89PNG fake")
    # hidden / skipped dirs
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("gitconfig")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "lib.js").write_text("module.exports = {}")
    return tmp_path


class TestListRepoTree:
    def test_returns_allowed_files(self, repo: Path) -> None:
        tree = list_repo_tree(repo, EXTS)
        assert "app/main.py" in tree or "app\\main.py" in tree
        assert "app/utils.py" in tree or "app\\utils.py" in tree
        assert "package.json" in tree
        assert "README.md" in tree

    def test_excludes_disallowed_extensions(self, repo: Path) -> None:
        tree = list_repo_tree(repo, EXTS)
        assert "logo.png" not in tree

    def test_skips_hidden_and_ignored_dirs(self, repo: Path) -> None:
        tree = list_repo_tree(repo, EXTS)
        assert ".git" not in tree
        assert "node_modules" not in tree

    def test_respects_max_depth(self, repo: Path) -> None:
        deep = repo / "a" / "b" / "c"
        deep.mkdir(parents=True)
        (deep / "deep.py").write_text("x = 1")
        tree = list_repo_tree(repo, EXTS, max_depth=1)
        assert "deep.py" not in tree

    def test_truncation(self, repo: Path) -> None:
        big_dir = repo / "big"
        big_dir.mkdir()
        for i in range(2000):
            (big_dir / f"file_{i:04d}.py").write_text(f"# {i}")
        tree = list_repo_tree(repo, EXTS)
        assert "截断" in tree

    def test_empty_repo(self, tmp_path: Path) -> None:
        result = list_repo_tree(tmp_path, EXTS)
        assert "没有找到" in result


class TestReadRepoFile:
    def test_reads_file(self, repo: Path) -> None:
        content = read_repo_file(repo, "app/main.py", EXTS)
        assert "print('hello')" in content

    def test_rejects_path_traversal(self, repo: Path) -> None:
        result = read_repo_file(repo, "../../etc/passwd", EXTS)
        assert "不合法" in result or "不允许" in result

    def test_rejects_disallowed_extension(self, repo: Path) -> None:
        result = read_repo_file(repo, "logo.png", EXTS)
        assert "不允许" in result

    def test_missing_file(self, repo: Path) -> None:
        result = read_repo_file(repo, "nonexistent.py", EXTS)
        assert "不存在" in result

    def test_truncates_large_file(self, repo: Path) -> None:
        big = repo / "big.py"
        big.write_text("x" * 60_000)
        content = read_repo_file(repo, "big.py", EXTS, max_chars=1000)
        assert len(content) < 2000
        assert "截断" in content


class TestSearchRepoFiles:
    def test_finds_by_name(self, repo: Path) -> None:
        result = search_repo_files(repo, "main", EXTS)
        assert "main.py" in result

    def test_case_insensitive(self, repo: Path) -> None:
        result = search_repo_files(repo, "README", EXTS)
        assert "README.md" in result

    def test_no_match(self, repo: Path) -> None:
        result = search_repo_files(repo, "nonexistent_xyz", EXTS)
        assert "没有找到" in result

    def test_empty_pattern(self, repo: Path) -> None:
        result = search_repo_files(repo, "  ", EXTS)
        assert "请提供" in result

    def test_max_results(self, repo: Path) -> None:
        bulk = repo / "bulk"
        bulk.mkdir()
        for i in range(40):
            (bulk / f"match_{i}.py").write_text("")
        result = search_repo_files(repo, "match_", EXTS, max_results=5)
        assert "截断" in result

    def test_skips_ignored_dirs(self, repo: Path) -> None:
        result = search_repo_files(repo, "lib.js", EXTS)
        assert "没有找到" in result


class TestGrepRepo:
    def test_finds_content(self, repo: Path) -> None:
        result = grep_repo(repo, "hello", EXTS)
        assert "main.py" in result
        assert "hello" in result

    def test_case_insensitive(self, repo: Path) -> None:
        result = grep_repo(repo, "HELLO", EXTS)
        assert "main.py" in result

    def test_shows_line_numbers(self, repo: Path) -> None:
        result = grep_repo(repo, "return a + b", EXTS)
        assert ":2:" in result

    def test_no_match(self, repo: Path) -> None:
        result = grep_repo(repo, "zzz_no_match_zzz", EXTS)
        assert "没有" in result

    def test_empty_query(self, repo: Path) -> None:
        result = grep_repo(repo, "", EXTS)
        assert "请提供" in result

    def test_skips_ignored_dirs(self, repo: Path) -> None:
        result = grep_repo(repo, "module.exports", EXTS)
        assert "没有" in result
