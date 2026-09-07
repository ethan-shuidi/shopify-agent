import os
from pathlib import Path

SKIP_DIRS = frozenset({
    ".git", ".venv", "venv", "__pycache__", "node_modules",
    ".next", "dist", "build", ".cache", ".turbo", ".output",
})

MAX_TREE_CHARS = 30_000
MAX_FILE_CHARS = 50_000
MAX_GREP_CHARS = 30_000


def _should_skip_dir(name: str) -> bool:
    return name in SKIP_DIRS or name.startswith(".")


def _allowed(path: str, allowed_extensions: frozenset[str]) -> bool:
    for ext in allowed_extensions:
        if path.endswith(ext):
            return True
    return False


def _safe_resolve(repo_root: Path, relative_path: str) -> Path | None:
    try:
        resolved = (repo_root / relative_path).resolve()
    except (OSError, ValueError):
        return None
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError:
        return None
    return resolved


def list_repo_tree(
    repo_root: Path,
    allowed_extensions: frozenset[str],
    max_depth: int = 8,
) -> str:
    lines: list[str] = []
    root = repo_root.resolve()
    total_chars = 0

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d for d in dirnames
            if not _should_skip_dir(d)
        )

        rel_dir = os.path.relpath(dirpath, root)
        depth = 0 if rel_dir == "." else rel_dir.count(os.sep) + 1
        if depth > max_depth:
            dirnames.clear()
            continue

        for fname in sorted(filenames):
            rel_path = os.path.join(rel_dir, fname) if rel_dir != "." else fname
            if not _allowed(rel_path, allowed_extensions):
                continue
            line = rel_path + "\n"
            total_chars += len(line)
            if total_chars > MAX_TREE_CHARS:
                lines.append("... [文件列表过长，已截断。请使用 search_repo_files 缩小范围]\n")
                return "".join(lines)
            lines.append(line)

    if not lines:
        return "仓库中没有找到匹配扩展名的文件。"
    return "".join(lines)


def read_repo_file(
    repo_root: Path,
    relative_path: str,
    allowed_extensions: frozenset[str],
    max_chars: int = MAX_FILE_CHARS,
) -> str:
    resolved = _safe_resolve(repo_root, relative_path)
    if resolved is None:
        return f"路径不合法: {relative_path}"

    if not _allowed(relative_path, allowed_extensions):
        return f"不允许读取该类型的文件: {relative_path}"

    if not resolved.is_file():
        return f"文件不存在: {relative_path}"

    try:
        content = resolved.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"读取文件失败: {exc}"

    if len(content) > max_chars:
        return content[:max_chars] + "\n\n... [文件内容过长，已截断]"
    return content


def search_repo_files(
    repo_root: Path,
    pattern: str,
    allowed_extensions: frozenset[str],
    max_results: int = 30,
) -> str:
    if not pattern.strip():
        return "请提供搜索关键词。"

    pattern_lower = pattern.lower()
    root = repo_root.resolve()
    matches: list[str] = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not _should_skip_dir(d)]
        for fname in filenames:
            rel_path = os.path.relpath(os.path.join(dirpath, fname), root)
            if not _allowed(rel_path, allowed_extensions):
                continue
            if pattern_lower in rel_path.lower():
                matches.append(rel_path)
                if len(matches) >= max_results:
                    matches.append(f"... [结果超过 {max_results} 条，已截断]")
                    return "\n".join(matches)

    if not matches:
        return f"没有找到匹配 '{pattern}' 的文件。"
    return "\n".join(matches)


def grep_repo(
    repo_root: Path,
    query: str,
    allowed_extensions: frozenset[str],
    max_results: int = 30,
) -> str:
    if not query.strip():
        return "请提供搜索关键词。"

    query_lower = query.lower()
    root = repo_root.resolve()
    results: list[str] = []
    total_chars = 0

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not _should_skip_dir(d)]
        for fname in filenames:
            full_path = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(full_path, root)
            if not _allowed(rel_path, allowed_extensions):
                continue
            try:
                with open(full_path, encoding="utf-8", errors="replace") as f:
                    for lineno, line in enumerate(f, 1):
                        if query_lower in line.lower():
                            entry = f"{rel_path}:{lineno}: {line.rstrip()}"
                            total_chars += len(entry) + 1
                            results.append(entry)
                            if len(results) >= max_results or total_chars > MAX_GREP_CHARS:
                                results.append("... [结果过多，已截断]")
                                return "\n".join(results)
            except OSError:
                continue

    if not results:
        return f"没有在文件内容中找到 '{query}'。"
    return "\n".join(results)
