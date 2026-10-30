"""Klaviyo API tools for listing metrics and exporting event data."""

import queue
import subprocess
import sys
import tempfile
from pathlib import Path

import requests

REVISION = "2026-10-15"
API_BASE = "https://a.klaviyo.com/api"

from app.config import get_settings


def _get_klaviyo_key(site: str) -> str:
    settings = get_settings()
    keys = {
        "us": settings.klaviyo_api_key_us.get_secret_value(),
        "jp": settings.klaviyo_api_key_jp.get_secret_value(),
        "eu": settings.klaviyo_api_key_eu.get_secret_value(),
    }
    return keys.get(site, "")

EXPORT_SCRIPT = (
    Path.home() / ".codex/skills/klaviyo-site-export/scripts/export_klaviyo.py"
)

_pending_files: queue.Queue[Path] = queue.Queue()


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Klaviyo-API-Key {api_key}",
        "accept": "application/vnd.api+json",
        "revision": REVISION,
    }


def list_klaviyo_metrics(site: str) -> str:
    api_key = _get_klaviyo_key(site)
    if not api_key:
        return f"未知站点: {site}，可选: us, jp, eu"

    try:
        resp = requests.get(
            f"{API_BASE}/metrics", headers=_headers(api_key), timeout=30,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        return f"请求 Klaviyo 失败: {exc}"

    metrics = resp.json().get("data", [])
    if not metrics:
        return f"站点 {site} 没有找到任何 metric。"

    lines = [f"站点 {site} 共有 {len(metrics)} 个 metric：\n"]
    for m in metrics:
        attrs = m.get("attributes", {})
        lines.append(f"- **{attrs.get('name', '?')}**  ID: `{m['id']}`")
    return "\n".join(lines)


def export_klaviyo_events(site: str, metric_ids: str) -> str:
    """Export events for the given site and metric IDs (comma-separated)."""
    if not _get_klaviyo_key(site):
        return f"未知站点: {site}，可选: us, jp, eu"

    ids = [mid.strip() for mid in metric_ids.split(",") if mid.strip()]
    if not ids:
        return "请提供至少一个 Metric ID。"

    if not EXPORT_SCRIPT.is_file():
        return f"导出脚本不存在: {EXPORT_SCRIPT}"

    args = [sys.executable, str(EXPORT_SCRIPT), "--site", site]
    for mid in ids:
        args.extend(["--metric-id", mid])
    args.extend(["--output-dir", tempfile.mkdtemp(prefix="klaviyo_")])

    try:
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=600,
        )
    except subprocess.TimeoutExpired:
        return "导出超时（10 分钟），数据量可能过大。"

    output = result.stdout.strip()
    if result.returncode != 0:
        err = result.stderr.strip()
        return f"导出失败:\n{err or output}"

    # Parse folder path from script output and find the CSV
    for line in output.splitlines():
        if line.startswith("文件位置："):
            folder = Path(line.split("：", 1)[1].strip())
            csv_path = folder / "events.csv"
            if csv_path.is_file():
                _pending_files.put(csv_path)
    return output


def pop_pending_file() -> Path | None:
    """Retrieve and clear any CSV file path left by the last export."""
    try:
        return _pending_files.get_nowait()
    except queue.Empty:
        return None
