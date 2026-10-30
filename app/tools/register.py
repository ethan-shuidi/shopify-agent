from pathlib import Path

from pydantic_ai import Agent

from app.tools.klaviyo import export_klaviyo_events, list_klaviyo_metrics
from app.tools.shopify import (
    get_shopify_sales_summary,
    list_shopify_orders,
    list_shopify_products,
    search_shopify_orders,
)
from app.tools.repo_read import (
    grep_repo,
    list_repo_tree,
    read_repo_file,
    search_repo_files,
    switch_repo_branch,
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
        name="switch_repo_branch",
        description=(
            "切换代码仓库到指定的 Git 分支。"
            "参数 branch 是分支名，例如 'live-us'。"
        ),
    )
    def _switch_branch(branch: str) -> str:
        return switch_repo_branch(repo_root, branch)

    @agent.tool_plain(
        name="grep_repo",
        description=(
            "在仓库文件内容中搜索包含指定文本的行。"
            "参数 query 是要搜索的字符串，例如函数名、变量名或错误信息。"
        ),
    )
    def _grep(query: str) -> str:
        return grep_repo(repo_root, query, allowed_extensions)


def register_klaviyo_tools(agent: Agent) -> None:
    @agent.tool_plain(
        name="list_klaviyo_metrics",
        description=(
            "列出指定站点在 Klaviyo 中的所有 metric 及其 ID。"
            "参数 site 是站点标识：us、jp 或 eu。"
        ),
    )
    def _list_metrics(site: str) -> str:
        return list_klaviyo_metrics(site)

    @agent.tool_plain(
        name="export_klaviyo_events",
        description=(
            "导出指定站点和 Metric ID 的 Klaviyo 事件数据到桌面 CSV 文件。"
            "参数 site 是站点标识（us、jp、eu），"
            "metric_ids 是一个或多个 Metric ID，用逗号分隔。"
        ),
    )
    def _export_events(site: str, metric_ids: str) -> str:
        return export_klaviyo_events(site, metric_ids)


def register_shopify_tools(agent: Agent) -> None:
    @agent.tool_plain(
        name="list_shopify_orders",
        description=(
            "查询指定站点最近的 Shopify 订单。"
            "参数 site 是站点标识（us、jp、eu），"
            "limit 是返回数量（默认 10，最多 50），"
            "status 是订单状态（any、open、closed、cancelled，默认 any）。"
        ),
    )
    def _list_orders(site: str, limit: int = 10, status: str = "any") -> str:
        return list_shopify_orders(site, limit, status)

    @agent.tool_plain(
        name="search_shopify_orders",
        description=(
            "按订单号、客户姓名或邮箱搜索 Shopify 订单。"
            "参数 site 是站点标识，query 是搜索关键词（如 '#1001' 或客户名）。"
        ),
    )
    def _search_orders(site: str, query: str) -> str:
        return search_shopify_orders(site, query)

    @agent.tool_plain(
        name="list_shopify_products",
        description=(
            "查询指定站点的 Shopify 产品列表。"
            "参数 site 是站点标识，limit 是返回数量（默认 10，最多 50）。"
        ),
    )
    def _list_products(site: str, limit: int = 10) -> str:
        return list_shopify_products(site, limit)

    @agent.tool_plain(
        name="get_shopify_sales_summary",
        description=(
            "查询指定站点最近 N 天的销售汇总（订单数、总销售额、平均客单价等）。"
            "参数 site 是站点标识，days 是天数（默认 7）。"
        ),
    )
    def _sales_summary(site: str, days: int = 7) -> str:
        return get_shopify_sales_summary(site, days)
