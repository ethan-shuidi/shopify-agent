"""Shopify Admin API tools for querying orders, products, and sales data."""

import threading
import time
from datetime import datetime, timedelta, timezone

import requests

API_VERSION = "2024-10"

from app.config import get_settings

SHOPS: dict[str, str] = {
    "us": "bhuvt5-ds.myshopify.com",
    "jp": "comu-jp.myshopify.com",
    "eu": "comu-eu-10dzpjm1.myshopify.com",
}


class _TokenCache:
    """Thread-safe token cache with auto-refresh."""

    def __init__(self) -> None:
        self._tokens: dict[str, tuple[str, float]] = {}
        self._lock = threading.Lock()

    def get(self, site: str) -> str | None:
        shop = SHOPS.get(site)
        if not shop:
            return None
        with self._lock:
            cached = self._tokens.get(site)
            if cached and cached[1] > time.time():
                return cached[0]
        token = self._fetch(shop)
        if token:
            with self._lock:
                # Cache for 23 hours (token lasts 24h)
                self._tokens[site] = (token, time.time() + 82800)
        return token

    def _fetch(self, shop: str) -> str | None:
        settings = get_settings()
        try:
            resp = requests.post(
                f"https://{shop}/admin/oauth/access_token",
                json={
                    "grant_type": "client_credentials",
                    "client_id": settings.shopify_client_id,
                    "client_secret": settings.shopify_client_secret.get_secret_value(),
                },
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json().get("access_token")
        except requests.RequestException:
            return None


_cache = _TokenCache()


def _api_get(site: str, endpoint: str, params: dict | None = None) -> dict | str:
    shop = SHOPS.get(site)
    if not shop:
        return f"未知站点: {site}，可选: us, jp, eu"
    token = _cache.get(site)
    if not token:
        return f"获取 {site} 站 Shopify access token 失败，请检查 App 配置和权限。"
    try:
        resp = requests.get(
            f"https://{shop}/admin/api/{API_VERSION}/{endpoint}",
            headers={"X-Shopify-Access-Token": token},
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        return f"Shopify API 请求失败: {exc}"


def list_shopify_orders(site: str, limit: int = 10, status: str = "any") -> str:
    result = _api_get(site, "orders.json", {
        "limit": min(limit, 50),
        "status": status,
        "order": "created_at desc",
    })
    if isinstance(result, str):
        return result
    orders = result.get("orders", [])
    if not orders:
        return f"站点 {site} 没有找到订单。"
    lines = [f"站点 {site} 最近 {len(orders)} 笔订单：\n"]
    for o in orders:
        name = o.get("name", "?")
        created = o.get("created_at", "")[:10]
        total = o.get("total_price", "0")
        currency = o.get("currency", "")
        status_val = o.get("financial_status", "")
        customer = o.get("customer", {})
        cname = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip() or "匿名"
        lines.append(f"- {name} | {created} | {total} {currency} | {status_val} | {cname}")
    return "\n".join(lines)


def list_shopify_products(site: str, limit: int = 10) -> str:
    result = _api_get(site, "products.json", {"limit": min(limit, 50)})
    if isinstance(result, str):
        return result
    products = result.get("products", [])
    if not products:
        return f"站点 {site} 没有找到产品。"
    lines = [f"站点 {site} 共 {len(products)} 个产品：\n"]
    for p in products:
        title = p.get("title", "?")
        status = p.get("status", "")
        variants = p.get("variants", [])
        price = variants[0].get("price", "?") if variants else "?"
        inventory = sum(v.get("inventory_quantity", 0) for v in variants)
        lines.append(f"- **{title}** | {price} | 库存: {inventory} | {status}")
    return "\n".join(lines)


def search_shopify_orders(site: str, query: str) -> str:
    """Search orders by order number, customer name, etc."""
    result = _api_get(site, "orders.json", {
        "status": "any",
        "limit": 20,
        "name": query if query.startswith("#") else None,
    })
    if isinstance(result, str):
        return result
    orders = result.get("orders", [])
    query_lower = query.lower().lstrip("#")
    matched = [
        o for o in orders
        if query_lower in o.get("name", "").lower()
        or query_lower in f"{o.get('customer', {}).get('first_name', '')} {o.get('customer', {}).get('last_name', '')}".lower()
        or query_lower in o.get("email", "").lower()
    ]
    if not matched:
        return f"站点 {site} 没有找到与 '{query}' 匹配的订单。"
    lines = [f"找到 {len(matched)} 笔匹配订单：\n"]
    for o in matched:
        name = o.get("name", "?")
        created = o.get("created_at", "")[:10]
        total = o.get("total_price", "0")
        currency = o.get("currency", "")
        status_val = o.get("financial_status", "")
        lines.append(f"- {name} | {created} | {total} {currency} | {status_val}")
    return "\n".join(lines)


def get_shopify_sales_summary(site: str, days: int = 7) -> str:
    """Aggregate sales from recent orders."""
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    result = _api_get(site, "orders.json", {
        "status": "any",
        "created_at_min": since,
        "limit": 250,
    })
    if isinstance(result, str):
        return result
    orders = result.get("orders", [])
    if not orders:
        return f"站点 {site} 最近 {days} 天没有订单。"

    total_sales = 0.0
    total_orders = len(orders)
    paid_orders = 0
    refunded_orders = 0
    currency = orders[0].get("currency", "") if orders else ""

    for o in orders:
        total_sales += float(o.get("total_price", 0))
        fs = o.get("financial_status", "")
        if fs == "paid":
            paid_orders += 1
        elif fs in {"refunded", "partially_refunded"}:
            refunded_orders += 1

    avg = total_sales / total_orders if total_orders else 0
    return (
        f"站点 {site} 最近 {days} 天销售汇总：\n\n"
        f"- 订单数：{total_orders}\n"
        f"- 总销售额：{total_sales:.2f} {currency}\n"
        f"- 平均客单价：{avg:.2f} {currency}\n"
        f"- 已支付：{paid_orders} 笔\n"
        f"- 已退款/部分退款：{refunded_orders} 笔"
    )
