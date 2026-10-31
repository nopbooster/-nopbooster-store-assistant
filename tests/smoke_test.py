"""
Fast check that runs in CI without Claude: starts the mock Booster AI server and
verifies auth, the documented tools, and the preview -> confirm -> apply flow.

    python tests/smoke_test.py
"""
import json, os, subprocess, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
URL = "http://127.0.0.1:8766/mcp/admin"
KEY = "ci-key"


def post(body, key=KEY, sid=None):
    h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if key:
        h["Authorization"] = f"Bearer {key}"
    if sid:
        h["mcp-session-id"] = sid
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            text = r.read().decode()
            data = [json.loads(l[5:]) for l in text.splitlines() if l.startswith("data:")]
            return r.status, (data[0] if data else None), r.headers.get("mcp-session-id")
    except urllib.error.HTTPError as e:
        return e.code, None, None


def call(sid, i, name, args):
    _, d, _ = post({"jsonrpc": "2.0", "id": i, "method": "tools/call", "params": {"name": name, "arguments": args}}, sid=sid)
    return json.loads(d["result"]["content"][0]["text"])


def main():
    proc = subprocess.Popen([sys.executable, os.path.join(HERE, "mock_booster_ai.py"), "--port", "8766", "--key", KEY])
    time.sleep(4)
    fails = []
    try:
        st, _, _ = post({}, key=None)
        if st != 401: fails.append(f"no key should be 401, got {st}")
        st, d, sid = post({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "ci", "version": "0"}}})
        post({"jsonrpc": "2.0", "method": "notifications/initialized"}, sid=sid)
        _, d, _ = post({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, sid=sid)
        names = {t["name"] for t in d["result"]["tools"]}
        for n in ("sales_report", "bulk_update_products", "search_orders", "update_order_status"):
            if n not in names: fails.append(f"missing tool {n}")
        if any("delete" in n for n in names): fails.append("a delete tool exists")
        prev = call(sid, 3, "bulk_update_products", {"product_ids": [2], "price_change_percent": 10})
        if not prev.get("preview"): fails.append("bulk update did not return a preview")
        tok = prev.get("confirmation_token")
        if call(sid, 4, "bulk_update_products", {"product_ids": [2], "confirmation_token": tok}).get("applied") is not True: fails.append("apply with token failed")
        if call(sid, 5, "bulk_update_products", {"product_ids": [2], "confirmation_token": tok}).get("error") != "invalid_or_used_token": fails.append("token was reusable")
    finally:
        proc.terminate()
    if fails:
        print("FAILED:", *fails, sep="\n - "); sys.exit(1)
    print("OK — auth, tools, preview/confirm/single-use token all behave as expected")


if __name__ == "__main__":
    main()
