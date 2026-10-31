"""
End-to-end test: runs Claude Code with this plugin against the mock Booster AI
server (tests/mock_booster_ai.py) and checks what actually reached the server.

Requires: Claude Code (`claude`) signed in, Python 3 with `mcp>=1.20,<2` and `uvicorn`.

    python tests/e2e_test.py

Scenarios
1. Weekly report      -> only read tools are called, authorised, and the answer uses the server's numbers
2. Price update        -> a preview is requested, nothing is applied without approval
3. Approve the preview -> the follow-up turn applies with the confirmation token; prices change
4. Wrong API key      -> the server rejects it and Claude reports the problem without inventing figures
"""

import json
import os
import signal
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS = os.path.join(ROOT, "tests")
LOG = os.path.join(TESTS, "calls.jsonl")
PORT = 8765
KEY = "test-key-123"
PREFIX = "mcp__plugin_nopbooster-store-assistant_booster-ai"
WRITE_TOOLS = {"update_order_status", "bulk_update_products", "update_product", "set_localized_strings",
               "update_seo", "update_topic", "create_product"}


def settings_file(key):
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump({"pluginConfigs": {"nopbooster-store-assistant@inline": {
        "options": {"store_url": f"http://127.0.0.1:{PORT}", "api_key": key}}}}, f)
    f.close()
    return f.name


def claude(prompt, settings, resume=None):
    env = dict(os.environ)
    for v in ("CLAUDE_CODE_SKIP_PLUGIN_MCP_SERVERS", "CLAUDE_CODE_CHILD_SESSION"):
        env.pop(v, None)
    cmd = ["claude", "-p", prompt, "--plugin-dir", ROOT, "--settings", settings,
           "--allowedTools", PREFIX, "Read", "--output-format", "json"]
    if resume:
        cmd += ["--resume", resume]
    out = subprocess.run(cmd, capture_output=True, text=True, env=env, stdin=subprocess.DEVNULL, timeout=900)
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError:
        print(out.stdout[-2000:], out.stderr[-2000:])
        raise


def calls():
    if not os.path.exists(LOG):
        return [], []
    tools, http = [], []
    for line in open(LOG, encoding="utf-8"):
        d = json.loads(line)
        (tools if d["kind"] == "tool" else http).append(d)
    return tools, http


def reset_log():
    if os.path.exists(LOG):
        os.remove(LOG)


def check(cond, msg, failures):
    print(("  PASS  " if cond else "  FAIL  ") + msg)
    if not cond:
        failures.append(msg)


def main():
    server = subprocess.Popen([sys.executable, os.path.join(TESTS, "mock_booster_ai.py"), "--port", str(PORT), "--key", KEY],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(4)
    failures = []
    good = settings_file(KEY)
    bad = settings_file("wrong-key")
    try:
        print("1. Weekly report")
        reset_log()
        r = claude("/nopbooster-store-assistant:nop-weekly-report last 7 days", good)
        tools, http = calls()
        names = [t["name"] for t in tools]
        check("sales_report" in names, "sales_report called", failures)
        check("bestsellers_report" in names and "low_stock_report" in names, "bestsellers and low-stock reports called", failures)
        check(not (set(names) & WRITE_TOOLS), "no write tools called", failures)
        check(http and all(h["auth_ok"] for h in http), "every request carried the right API key", failures)
        check("Running Shoes" in r.get("result", ""), "answer uses the server's data (bestseller 'Running Shoes')", failures)

        print("2. Price update, no approval")
        reset_log()
        r = claude("/nopbooster-store-assistant:nop-price-update Raise prices in the Accessories category by 10%, round to 2 decimals.", good)
        session = r.get("session_id")
        tools, _ = calls()
        bulk = [t for t in tools if t["name"] == "bulk_update_products"]
        check(any(not t["args"]["has_token"] for t in bulk), "a preview was requested", failures)
        check(not any(t["args"]["has_token"] for t in bulk), "nothing applied without approval", failures)

        print("3. Approve the preview")
        reset_log()
        r = claude("Yes, I approve exactly that preview. Apply it.", good, resume=session)
        tools, _ = calls()
        bulk = [t for t in tools if t["name"] == "bulk_update_products"]
        check(any(t["args"]["has_token"] for t in bulk), "change applied with the confirmation token", failures)
        reset_log()
        r2 = claude("Use search_products for the Accessories category and tell me the current price of Leather Wallet. Just the number.", good)
        check("43.89" in r2.get("result", ""), "Leather Wallet price is now 43.89 (39.90 + 10%)", failures)

        print("4. Wrong API key")
        reset_log()
        r = claude("/nopbooster-store-assistant:nop-weekly-report last 7 days", bad)
        _, http = calls()
        text = r.get("result", "").lower()
        check(not any(h["auth_ok"] for h in http), "server saw no valid key", failures)
        check("running shoes" not in text, "no figures invented", failures)
        check(any(w in text for w in ("key", "unauthor", "401", "authori")), "the key problem is reported", failures)
    finally:
        server.send_signal(signal.SIGTERM)
        for f in (good, bad):
            os.remove(f)

    print()
    if failures:
        print(f"FAILED: {len(failures)} check(s)")
        sys.exit(1)
    print("ALL END-TO-END CHECKS PASSED")


if __name__ == "__main__":
    main()
