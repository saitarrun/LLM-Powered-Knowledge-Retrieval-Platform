#!/usr/bin/env python3
"""
Nexus Smoke Test Suite
Runs after every merge to main. Tests that the full application stack
is running correctly. Results are sent to Claude for analysis and
a report is posted back to GitHub.
"""

import os, sys, json, time, httpx, subprocess, traceback

OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
GITHUB_TOKEN       = os.environ["GITHUB_TOKEN"]
REPO               = os.environ["GITHUB_REPOSITORY"]
COMMIT_SHA         = os.environ.get("GITHUB_SHA", "")
COMMIT_MESSAGE     = os.environ.get("COMMIT_MESSAGE", "")
RUN_URL            = os.environ.get("RUN_URL", f"https://github.com/{os.environ.get('GITHUB_REPOSITORY','')}/actions")

BACKEND_URL  = "http://localhost:8001"
FRONTEND_URL = "http://localhost:3001"
NEO4J_URL    = "http://localhost:7474"

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL          = "anthropic/claude-sonnet-4-5"
GH_API         = "https://api.github.com"

HEADERS_GH = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
HEADERS_OR = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": f"https://github.com/{REPO}",
    "X-Title": "Nexus Smoke Tests",
}

# ── Test runner ────────────────────────────────────────────────────────────────

def run_test(name, fn):
    """Execute a single test, catch all exceptions, return result dict."""
    start = time.time()
    try:
        result = fn()
        return {
            "name": name,
            "status": "PASS" if result.get("ok") else "FAIL",
            "latency_ms": round((time.time() - start) * 1000),
            "detail": result.get("detail", ""),
            "response": result.get("response", ""),
        }
    except Exception as e:
        return {
            "name": name,
            "status": "FAIL",
            "latency_ms": round((time.time() - start) * 1000),
            "detail": str(e),
            "response": traceback.format_exc(),
        }

# ── Individual tests ───────────────────────────────────────────────────────────

def test_backend_health():
    r = httpx.get(f"{BACKEND_URL}/api/health", timeout=10)
    body = r.json()
    ok = r.status_code == 200 and body.get("status") == "healthy"
    return {"ok": ok, "detail": f"HTTP {r.status_code}", "response": json.dumps(body)}

def test_backend_openapi():
    r = httpx.get(f"{BACKEND_URL}/api/v1/openapi.json", timeout=10)
    ok = r.status_code == 200 and "openapi" in r.json()
    return {"ok": ok, "detail": f"HTTP {r.status_code}, paths: {len(r.json().get('paths', {}))}"}

def test_documents_list():
    r = httpx.get(f"{BACKEND_URL}/api/v1/documents", timeout=15)
    ok = r.status_code == 200
    body = r.text[:500]
    return {"ok": ok, "detail": f"HTTP {r.status_code}", "response": body}

def test_settings_endpoint():
    r = httpx.get(f"{BACKEND_URL}/api/v1/settings", timeout=10)
    ok = r.status_code in (200, 404)  # 404 = route exists but no settings yet
    return {"ok": ok, "detail": f"HTTP {r.status_code}"}

def test_chat_endpoint_reachable():
    """Verify the chat endpoint exists and accepts POST (even if it errors without a real query)."""
    r = httpx.post(
        f"{BACKEND_URL}/api/v1/chat",
        json={"message": "ping", "conversation_id": "smoke-test"},
        timeout=30,
    )
    # 200 = works, 422 = validation error (endpoint exists), 500 = server error
    ok = r.status_code in (200, 422)
    return {"ok": ok, "detail": f"HTTP {r.status_code}", "response": r.text[:300]}

def test_frontend_loads():
    r = httpx.get(FRONTEND_URL, timeout=20)
    ok = r.status_code == 200 and len(r.text) > 100
    return {"ok": ok, "detail": f"HTTP {r.status_code}, body size: {len(r.text)} bytes"}

def test_neo4j_reachable():
    r = httpx.get(f"{NEO4J_URL}", timeout=10)
    ok = r.status_code == 200
    return {"ok": ok, "detail": f"HTTP {r.status_code}"}

def test_redis_reachable():
    """Check Redis via backend health or direct ping if redis-cli is available."""
    result = subprocess.run(
        ["redis-cli", "-p", "6380", "ping"],
        capture_output=True, text=True, timeout=5
    )
    ok = result.stdout.strip() == "PONG"
    return {"ok": ok, "detail": f"redis-cli ping: {result.stdout.strip() or result.stderr.strip()}"}

def test_document_upload():
    """Upload a tiny test document and verify it's accepted."""
    import io
    fake_pdf = b"%PDF-1.4 smoke test document"
    r = httpx.post(
        f"{BACKEND_URL}/api/v1/documents/upload",
        files={"file": ("smoke_test.txt", io.BytesIO(b"Nexus smoke test document content."), "text/plain")},
        timeout=30,
    )
    ok = r.status_code in (200, 201, 202, 422)  # 422 = validation (file type), still reachable
    return {"ok": ok, "detail": f"HTTP {r.status_code}", "response": r.text[:300]}

def test_cors_headers():
    """Verify CORS headers are present for frontend origin."""
    r = httpx.options(
        f"{BACKEND_URL}/api/health",
        headers={"Origin": "http://localhost:3001", "Access-Control-Request-Method": "GET"},
        timeout=10,
    )
    has_cors = "access-control-allow-origin" in {k.lower() for k in r.headers}
    return {"ok": has_cors, "detail": f"HTTP {r.status_code}, CORS header present: {has_cors}"}

def test_no_secrets_in_response():
    """Verify health endpoint doesn't leak env vars or secrets."""
    r = httpx.get(f"{BACKEND_URL}/api/health", timeout=10)
    body = r.text.lower()
    leaked = any(kw in body for kw in ["sk-", "password", "secret", "api_key"])
    return {"ok": not leaked, "detail": "No secrets leaked" if not leaked else "⚠️ Potential secret in response!"}

# ── Wait for stack to be ready ────────────────────────────────────────────────

def wait_for_backend(max_wait=120):
    print(f"⏳ Waiting for backend at {BACKEND_URL}/api/health ...")
    deadline = time.time() + max_wait
    while time.time() < deadline:
        try:
            r = httpx.get(f"{BACKEND_URL}/api/health", timeout=5)
            if r.status_code == 200:
                print(f"✅ Backend ready ({round(time.time() - (deadline - max_wait))}s)")
                return True
        except Exception:
            pass
        time.sleep(3)
    print("❌ Backend did not become ready in time")
    return False

def wait_for_frontend(max_wait=120):
    print(f"⏳ Waiting for frontend at {FRONTEND_URL} ...")
    deadline = time.time() + max_wait
    while time.time() < deadline:
        try:
            r = httpx.get(FRONTEND_URL, timeout=5)
            if r.status_code == 200:
                print(f"✅ Frontend ready")
                return True
        except Exception:
            pass
        time.sleep(3)
    print("❌ Frontend did not become ready in time")
    return False

# ── Claude analysis ────────────────────────────────────────────────────────────

ANALYSIS_SYSTEM = """You are the post-deploy health analyst for Nexus — an LLM-powered knowledge retrieval platform.

You receive automated smoke test results from after a merge to main.
Your job is to:
1. Determine if the application is healthy enough for production traffic
2. Diagnose the root cause of any failures with specific actionable guidance
3. Decide whether the merge should be REVERTED or can stay with a hotfix

Output format (GitHub Markdown):

## 🏥 Post-Deploy Health Report

**Commit:** `{sha}`
**Overall Status:** 🟢 HEALTHY | 🟡 DEGRADED | 🔴 CRITICAL

## Test Results
| Test | Status | Latency | Detail |
|------|--------|---------|--------|
(fill in every test)

## Diagnosis
(For each failure: what is broken, why it broke, and the exact fix)

## Recommendation
**STABLE — no action needed**
OR
**HOTFIX NEEDED — fix X before next deploy** (with exact code/config fix)
OR
**REVERT IMMEDIATELY — critical failure** (with revert command)

Be precise. Reference the commit message and likely cause if you can infer it."""

def ask_claude(system, user):
    payload = {
        "model": MODEL, "max_tokens": 4096,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    }
    r = httpx.post(OPENROUTER_URL, headers=HEADERS_OR, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def get_docker_logs():
    """Capture docker compose logs for failed services."""
    try:
        result = subprocess.run(
            ["docker", "compose", "logs", "--tail=50"],
            capture_output=True, text=True, timeout=30
        )
        return result.stdout[-5000:] if result.stdout else result.stderr[-2000:]
    except Exception as e:
        return f"Could not fetch docker logs: {e}"

# ── GitHub helpers ─────────────────────────────────────────────────────────────

def post_commit_comment(sha, body):
    httpx.post(
        f"{GH_API}/repos/{REPO}/commits/{sha}/comments",
        headers=HEADERS_GH, json={"body": body}, timeout=30
    ).raise_for_status()

def create_issue(title, body, labels):
    httpx.post(
        f"{GH_API}/repos/{REPO}/issues",
        headers=HEADERS_GH, json={"title": title, "body": body, "labels": labels}, timeout=30
    ).raise_for_status()

def revert_commit(sha, message):
    subprocess.run(["git", "config", "user.email", "claude-bot@nexus.ai"], check=True)
    subprocess.run(["git", "config", "user.name", "Claude Bot"], check=True)
    subprocess.run(["git", "revert", "--no-edit", sha], check=True)
    subprocess.run(["git", "push", f"https://x-access-token:{GITHUB_TOKEN}@github.com/{REPO}.git", "main"], check=True)
    print(f"🔄 Reverted commit {sha}")

# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Nexus Smoke Test Suite")
    print(f"   Commit: {COMMIT_SHA[:10]}")
    print(f"   Message: {COMMIT_MESSAGE[:80]}")
    print("=" * 60)

    # Wait for services
    backend_up  = wait_for_backend()
    frontend_up = wait_for_frontend()

    # Run all tests
    ALL_TESTS = [
        ("Backend Health",          test_backend_health),
        ("OpenAPI Docs Accessible", test_backend_openapi),
        ("Documents List Endpoint", test_documents_list),
        ("Settings Endpoint",       test_settings_endpoint),
        ("Chat Endpoint Reachable", test_chat_endpoint_reachable),
        ("Document Upload Route",   test_document_upload),
        ("CORS Headers",            test_cors_headers),
        ("No Secrets Leaked",       test_no_secrets_in_response),
        ("Frontend Loads",          test_frontend_loads),
        ("Neo4j Reachable",         test_neo4j_reachable),
        ("Redis Reachable",         test_redis_reachable),
    ]

    if not backend_up:
        # Backend never came up — skip most tests
        results = [{"name": "Backend Health", "status": "FAIL", "latency_ms": 120000,
                    "detail": "Backend never became healthy after 120s", "response": ""}]
    else:
        results = []
        for name, fn in ALL_TESTS:
            r = run_test(name, fn)
            icon = "✅" if r["status"] == "PASS" else "❌"
            print(f"  {icon} {name} ({r['latency_ms']}ms) — {r['detail']}")
            results.append(r)

    # Summary
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    critical_failures = [r for r in results if r["status"] == "FAIL" and
                         r["name"] in ("Backend Health", "Frontend Loads", "Chat Endpoint Reachable")]

    print(f"📊 Results: {passed} passed, {failed} failed")

    # Get docker logs for context if there are failures
    docker_logs = ""
    if failed > 0:
        print("📋 Fetching docker logs...")
        docker_logs = get_docker_logs()

    # Build test table for Claude
    table_rows = "\n".join(
        f"| {r['name']} | {'✅ PASS' if r['status'] == 'PASS' else '❌ FAIL'} | {r['latency_ms']}ms | {r['detail']} |"
        for r in results
    )

    failure_details = "\n\n".join(
        f"### ❌ {r['name']}\n**Detail:** {r['detail']}\n**Response:**\n```\n{r['response'][:500]}\n```"
        for r in results if r["status"] == "FAIL"
    )

    user_msg = f"""## Smoke Test Results

**Commit:** `{COMMIT_SHA}`
**Commit message:** {COMMIT_MESSAGE}
**Run:** {RUN_URL}
**Backend started:** {'Yes' if backend_up else 'NO — never became healthy'}
**Frontend started:** {'Yes' if frontend_up else 'NO — never became healthy'}
**Summary:** {passed}/{len(results)} tests passed

## Test Table
| Test | Status | Latency | Detail |
|------|--------|---------|--------|
{table_rows}

## Failure Details
{failure_details or 'None — all tests passed!'}

## Docker Logs (last 50 lines)
```
{docker_logs[:3000] if docker_logs else 'No logs captured'}
```"""

    print("🤖 Asking Claude to analyze results...")
    analysis = ask_claude(ANALYSIS_SYSTEM.replace("{sha}", COMMIT_SHA[:10]), user_msg)

    header = (
        f"## 🤖 Claude Post-Deploy Health Report\n\n"
        f"> **Commit:** `{COMMIT_SHA[:10]}` · "
        f"**Tests:** {passed}/{len(results)} passed · "
        f"[Workflow run]({RUN_URL})\n\n---\n\n"
    )
    full_report = header + analysis

    # Post as commit comment
    if COMMIT_SHA:
        try:
            post_commit_comment(COMMIT_SHA, full_report)
            print("✅ Posted health report as commit comment")
        except Exception as e:
            print(f"⚠️  Could not post commit comment: {e}")

    # If critical failures — open an issue and optionally revert
    if critical_failures:
        issue_title = f"🚨 Post-deploy failure on {COMMIT_SHA[:8]}: {', '.join(r['name'] for r in critical_failures)}"
        issue_body  = (
            f"**Automatic issue opened by Claude** after detecting critical failures "
            f"following merge of `{COMMIT_SHA[:10]}`.\n\n"
            f"**Commit message:** {COMMIT_MESSAGE}\n\n"
            f"---\n\n{analysis}\n\n"
            f"**To revert:**\n```bash\ngit revert {COMMIT_SHA}\ngit push\n```"
        )
        try:
            create_issue(issue_title, issue_body, ["bug", "critical"])
            print(f"🚨 Opened critical issue: {issue_title}")
        except Exception as e:
            print(f"⚠️  Could not open issue: {e}")

        # Auto-revert if backend never came up at all (catastrophic)
        if not backend_up and os.environ.get("AUTO_REVERT") == "true":
            print("🔄 Backend is completely down — auto-reverting...")
            try:
                revert_commit(COMMIT_SHA, f"Revert: backend down after {COMMIT_SHA[:8]}")
                print("✅ Auto-revert successful")
            except Exception as e:
                print(f"❌ Auto-revert failed: {e}")

    # Exit with failure code if critical tests failed (so GH Actions marks the run red)
    if failed > 0:
        sys.exit(1)
