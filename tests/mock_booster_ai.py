"""
Stand-in for the MCP Server (Booster AI) nopCommerce plugin, for testing the
NopBooster Store Assistant plugin end to end without a real store.

It mimics the behaviours the plugin's skills rely on:
- remote MCP over HTTP at /mcp/admin
- Authorization: Bearer <key> required (401 otherwise)
- the documented tool names
- write tools return a preview + single-use confirmation token (10 min);
  applying needs that token; a stale token is refused
- no delete tools; customer contact details masked

Every request is appended to calls.jsonl next to this file so a test can
check what the client actually sent.

    python tests/mock_booster_ai.py --port 8765 --key test-key-123
"""

import argparse
import json
import os
import secrets
import time

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "calls.jsonl")

PRODUCTS = {
    1: {"id": 1, "name": "Leather Wallet", "sku": "LW-01", "price": 39.90, "stock": 4, "published": True,
        "category": "Accessories", "short_description": "", "meta_title": "", "meta_description": ""},
    2: {"id": 2, "name": "Canvas Tote", "sku": "CT-02", "price": 24.50, "stock": 120, "published": True,
        "category": "Accessories", "short_description": "Sturdy canvas tote bag.", "meta_title": "Canvas Tote",
        "meta_description": "A sturdy canvas tote for everyday use."},
    3: {"id": 3, "name": "Running Shoes", "sku": "RS-03", "price": 89.00, "stock": 2, "published": True,
        "category": "Shoes", "short_description": "Light running shoes.", "meta_title": "",
        "meta_description": ""},
}
ORDERS = {
    1042: {"number": 1042, "placed_days_ago": 6, "status": "Processing", "payment": "Paid", "shipping": "NotYetShipped", "total": 128.40},
    1043: {"number": 1043, "placed_days_ago": 5, "status": "Pending", "payment": "Pending", "shipping": "NotYetShipped", "total": 39.90},
    1050: {"number": 1050, "placed_days_ago": 1, "status": "Processing", "payment": "Paid", "shipping": "NotYetShipped", "total": 89.00},
}
PENDING = {}  # token -> (expires, action)

mcp = FastMCP("booster-ai-mock", streamable_http_path="/mcp/admin")


def _log(kind, payload):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"t": time.time(), "kind": kind, **payload}) + "\n")


def _preview(action, changes):
    token = secrets.token_hex(8)
    PENDING[token] = (time.time() + 600, action)
    return {"preview": True, "changes": changes, "confirmation_token": token,
            "expires_in_seconds": 600, "note": "Nothing has been written. Call again with confirmation_token to apply."}


def _take(token):
    item = PENDING.pop(token, None)
    if not item:
        return None, {"error": "invalid_or_used_token", "message": "Confirmation token is invalid, expired or already used. Request a new preview."}
    expires, action = item
    if time.time() > expires:
        return None, {"error": "token_expired", "message": "Confirmation token expired. Request a new preview."}
    return action, None


@mcp.tool()
def sales_report(start_date: str, end_date: str) -> dict:
    """Sales totals for a date range (inclusive, YYYY-MM-DD). Scope reports:read."""
    _log("tool", {"name": "sales_report", "args": {"start_date": start_date, "end_date": end_date}})
    seed = sum(map(ord, start_date)) % 7
    return {"start_date": start_date, "end_date": end_date, "currency": "USD",
            "orders": 90 + seed, "revenue": round(18000 + seed * 410.5, 2)}


@mcp.tool()
def bestsellers_report(start_date: str, end_date: str, top: int = 10) -> dict:
    """Best-selling products in a date range. Scope reports:read."""
    _log("tool", {"name": "bestsellers_report", "args": {"start_date": start_date, "end_date": end_date, "top": top}})
    return {"items": [{"product_id": 3, "name": "Running Shoes", "units": 40, "revenue": 3560.00},
                      {"product_id": 2, "name": "Canvas Tote", "units": 31, "revenue": 759.50},
                      {"product_id": 1, "name": "Leather Wallet", "units": 12, "revenue": 478.80}][:top]}


@mcp.tool()
def low_stock_report(top: int = 10) -> dict:
    """Products with the lowest stock. Scope reports:read."""
    _log("tool", {"name": "low_stock_report", "args": {"top": top}})
    items = sorted(PRODUCTS.values(), key=lambda p: p["stock"])[:top]
    return {"items": [{"product_id": p["id"], "name": p["name"], "stock": p["stock"]} for p in items]}


@mcp.tool()
def search_orders(status: str = "", older_than_days: int = 0) -> dict:
    """Search orders by status (Pending, Processing, Complete, Cancelled) and minimum age in days. Scope orders:read."""
    _log("tool", {"name": "search_orders", "args": {"status": status, "older_than_days": older_than_days}})
    res = [o for o in ORDERS.values()
           if (not status or o["status"].lower() == status.lower()) and o["placed_days_ago"] >= older_than_days]
    return {"orders": res}


@mcp.tool()
def update_order_status(order_number: int, new_status: str, confirmation_token: str = "") -> dict:
    """Change an order's status. Without confirmation_token returns a preview; with it, applies. Scope orders:write."""
    _log("tool", {"name": "update_order_status", "args": {"order_number": order_number, "new_status": new_status, "has_token": bool(confirmation_token)}})
    if order_number not in ORDERS:
        return {"error": "not_found"}
    if not confirmation_token:
        return _preview(("status", order_number, new_status),
                        [{"order": order_number, "field": "status", "before": ORDERS[order_number]["status"], "after": new_status}])
    action, err = _take(confirmation_token)
    if err:
        return err
    ORDERS[action[1]]["status"] = action[2]
    return {"applied": True, "order": action[1], "status": action[2]}


@mcp.tool()
def add_order_note(order_number: int, note: str, visible_to_customer: bool = False) -> dict:
    """Add a note to an order. Internal notes apply immediately. Scope orders:write."""
    _log("tool", {"name": "add_order_note", "args": {"order_number": order_number, "visible_to_customer": visible_to_customer}})
    return {"applied": True, "order": order_number, "visible_to_customer": visible_to_customer}


@mcp.tool()
def search_products(query: str = "", category: str = "", max_price: float = 0) -> dict:
    """Search products by name text, category and maximum price. Scope catalog:read."""
    _log("tool", {"name": "search_products", "args": {"query": query, "category": category, "max_price": max_price}})
    res = [p for p in PRODUCTS.values()
           if query.lower() in p["name"].lower()
           and (not category or p["category"].lower() == category.lower())
           and (not max_price or p["price"] <= max_price)]
    return {"products": res}


@mcp.tool()
def bulk_update_products(product_ids: list[int], price: float = 0, price_change_percent: float = 0,
                         confirmation_token: str = "") -> dict:
    """Update price for up to 200 products: set price, or change by a percentage. Preview first, then apply with confirmation_token. Scope catalog:write."""
    _log("tool", {"name": "bulk_update_products", "args": {"product_ids": product_ids, "price": price,
                                                           "price_change_percent": price_change_percent, "has_token": bool(confirmation_token)}})
    if len(product_ids) > 200:
        return {"error": "too_many_items", "message": "At most 200 products per call."}
    if not confirmation_token:
        changes = []
        for pid in product_ids:
            p = PRODUCTS.get(pid)
            if not p:
                continue
            new = price if price else round(p["price"] * (1 + price_change_percent / 100), 2)
            changes.append({"product_id": pid, "name": p["name"], "field": "price", "before": p["price"], "after": new})
        return _preview(("bulk", changes), changes)
    action, err = _take(confirmation_token)
    if err:
        return err
    for c in action[1]:
        PRODUCTS[c["product_id"]]["price"] = c["after"]
    return {"applied": True, "count": len(action[1])}


@mcp.tool()
def list_untranslated(language: str = "") -> dict:
    """List content missing a translation, per language. Scope content:read."""
    _log("tool", {"name": "list_untranslated", "args": {"language": language}})
    return {"language": language or "all", "missing": [{"entity": "Product", "id": 1, "field": "Name", "languages": ["ar", "de"]}]}


@mcp.tool()
def find_customer(email: str) -> dict:
    """Find a customer by e-mail. Contact details are masked without customers:pii. Scope customers:read."""
    _log("tool", {"name": "find_customer", "args": {"email": "***"}})
    return {"customer": {"id": 77, "email": "j***@e***.com", "phone": "***", "orders": 3}}


class AuthAndLog(BaseHTTPMiddleware):
    def __init__(self, app, key):
        super().__init__(app)
        self.key = key

    async def dispatch(self, request, call_next):
        auth = request.headers.get("authorization", "")
        _log("http", {"method": request.method, "path": request.url.path, "auth_ok": auth == f"Bearer {self.key}"})
        if auth != f"Bearer {self.key}":
            return JSONResponse({"error": "unauthorized", "message": "Missing or invalid API key."}, status_code=401)
        return await call_next(request)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--key", default="test-key-123")
    a = ap.parse_args()
    if os.path.exists(LOG):
        os.remove(LOG)
    app = mcp.streamable_http_app()
    app.add_middleware(AuthAndLog, key=a.key)
    uvicorn.run(app, host="127.0.0.1", port=a.port, log_level="warning")


if __name__ == "__main__":
    main()
