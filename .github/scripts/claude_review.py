#!/usr/bin/env python3
"""
Claude PR Reviewer (via OpenRouter) — runs inside GitHub Actions.
Fetches the PR diff, sends it to Claude through OpenRouter, and posts a detailed review.
Also handles /claude commands in PR comments for on-demand responses.
"""

import os
import sys
import httpx

# ── Config ─────────────────────────────────────────────────────────────────────
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
GITHUB_TOKEN       = os.environ["GITHUB_TOKEN"]
REPO               = os.environ["GITHUB_REPOSITORY"]
PR_NUMBER          = os.environ.get("PR_NUMBER", "")
EVENT_NAME         = os.environ.get("GITHUB_EVENT_NAME", "")
COMMENT_BODY       = os.environ.get("COMMENT_BODY", "")

# OpenRouter endpoint (OpenAI-compatible)
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL          = "anthropic/claude-sonnet-4-5"   # best Claude available on OpenRouter

GH_API      = "https://api.github.com"
HEADERS_GH  = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
HEADERS_OR  = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": f"https://github.com/{REPO}",
    "X-Title": "Nexus PR Reviewer",
}

# ── GitHub helpers ─────────────────────────────────────────────────────────────
def gh_get(path):
    r = httpx.get(f"{GH_API}{path}", headers=HEADERS_GH, timeout=30)
    r.raise_for_status()
    return r.json()

def gh_post(path, payload):
    r = httpx.post(f"{GH_API}{path}", headers=HEADERS_GH, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()

def gh_put(path, payload):
    r = httpx.put(f"{GH_API}{path}", headers=HEADERS_GH, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()

def get_pr_diff(pr_number):
    headers = {**HEADERS_GH, "Accept": "application/vnd.github.v3.diff"}
    r = httpx.get(f"{GH_API}/repos/{REPO}/pulls/{pr_number}", headers=headers, timeout=30)
    r.raise_for_status()
    return r.text

def get_pr_info(pr_number):
    return gh_get(f"/repos/{REPO}/pulls/{pr_number}")

def post_pr_comment(pr_number, body):
    gh_post(f"/repos/{REPO}/issues/{pr_number}/comments", {"body": body})

def post_pr_review(pr_number, body, event="COMMENT"):
    gh_post(f"/repos/{REPO}/pulls/{pr_number}/reviews", {"body": body, "event": event})

def merge_pr(pr_number, title, sha):
    gh_put(f"/repos/{REPO}/pulls/{pr_number}/merge", {
        "commit_title": title,
        "sha": sha,
        "merge_method": "squash",
    })

def get_check_runs(sha):
    data = gh_get(f"/repos/{REPO}/commits/{sha}/check-runs")
    return data.get("check_runs", [])

# ── OpenRouter / Claude helper ─────────────────────────────────────────────────
def ask_claude(system_prompt, user_message):
    payload = {
        "model": MODEL,
        "max_tokens": 4096,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
    }
    r = httpx.post(OPENROUTER_URL, headers=HEADERS_OR, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

# ── Review prompt ──────────────────────────────────────────────────────────────
REVIEW_SYSTEM = """You are an expert code reviewer for the **Nexus** project — an LLM-powered knowledge retrieval platform built with FastAPI (Python) + Next.js (TypeScript) + FAISS + Neo4j.

Review pull requests across these dimensions:

1. **Correctness** — bugs, off-by-one errors, wrong logic, unhandled edge cases
2. **Security** — injection risks, exposed secrets, auth bypasses, OWASP top 10
3. **Performance** — N+1 DB queries, blocking async calls, unnecessary re-renders
4. **Code Quality** — readability, naming, duplication, over-engineering
5. **Tests** — are tests added/updated for the changed code?
6. **Breaking Changes** — API contract changes, DB schema changes without migrations

Format your response in GitHub Markdown:

## Summary
(2–3 sentences on what the PR does and overall quality)

## Issues Found
### 🔴 Critical
(bugs, security issues, data loss risks — must fix before merge)

### 🟡 Warnings
(non-blocking but important: missing tests, performance concerns, unclear naming)

### 🟢 Suggestions
(optional improvements, style, nice-to-haves)

## Verdict
**APPROVE ✅** | **REQUEST_CHANGES ❌** | **NEEDS_DISCUSSION 💬**

(one sentence explaining your verdict)

Be direct and reference file paths and line numbers where possible. If the diff is clean with no issues, say so clearly."""

def review_pr(pr_number):
    pr   = get_pr_info(pr_number)
    diff = get_pr_diff(pr_number)
    head_sha = pr["head"]["sha"]

    if len(diff) > 80_000:
        diff = diff[:80_000] + "

[... diff truncated due to size ...]"

    user_msg = f"""## Pull Request #{pr_number}: {pr['title']}

**Author:** {pr['user']['login']}
**Branch:** `{pr['head']['ref']}` → `{pr['base']['ref']}`
**Description:** {pr.get('body') or '(no description provided)'}
**Stats:** {pr['changed_files']} files changed · +{pr['additions']} additions · -{pr['deletions']} deletions
**Merge conflicts:** {'YES ⚠️' if pr.get('mergeable') is False else 'None detected'}

---

## Diff

```diff
{diff}
```"""

    review_body = ask_claude(REVIEW_SYSTEM, user_msg)

    event = "COMMENT"
    if "APPROVE ✅" in review_body or "**APPROVE" in review_body:
        event = "APPROVE"
    elif "REQUEST_CHANGES ❌" in review_body or "**REQUEST_CHANGES" in review_body:
        event = "REQUEST_CHANGES"

    header = (
        f"## 🤖 Claude Code Review

"
        f"> Automated review powered by [{MODEL}](https://openrouter.ai) via OpenRouter"
        f" · [Workflow run](https://github.com/{REPO}/actions)

---

"
    )
    post_pr_review(pr_number, header + review_body, event)
    print(f"✅ Posted review (event={event}) on PR #{pr_number}")

    # Auto-merge if approved and no conflicts
    if event == "APPROVE" and pr.get("mergeable") is not False:
        checks   = get_check_runs(head_sha)
        failed   = [c for c in checks if c["conclusion"] in ("failure", "timed_out")  and c["name"] != "Claude Code Review"]
        pending  = [c for c in checks if c["status"]    in ("queued", "in_progress") and c["name"] != "Claude Code Review"]

        if failed:
            lines = "
".join(f"- `{c['name']}`: {c['conclusion']}" for c in failed)
            post_pr_comment(pr_number, f"⚠️ **Claude approved the code** but these CI checks are failing — fix them before merging:
{lines}")
        elif pending:
            post_pr_comment(pr_number, "⏳ **Claude approved this PR.** Waiting for other CI checks to finish before considering auto-merge.")
        else:
            try:
                merge_pr(pr_number, f"{pr['title']} (#{pr_number})", head_sha)
                post_pr_comment(
                    pr_number,
                    f"🎉 **Auto-merged by Claude!**

"
                    f"All checks passed and the review was clean.
"
                    f"Squash-merged `{pr['head']['ref']}` → `{pr['base']['ref']}`."
                )
                print(f"✅ Auto-merged PR #{pr_number}")
            except Exception as e:
                post_pr_comment(pr_number, f"✅ **Claude approved this PR** but auto-merge failed (may need maintainer merge):
```
{e}
```")

# ── /claude command handler ─────────────────────────────────────────────────────
COMMAND_SYSTEM = """You are Claude, an AI assistant embedded in the GitHub PR workflow for the Nexus LLM knowledge retrieval platform.
A developer has addressed you directly in a PR comment using `/claude`.
Answer helpfully, concisely, and with concrete actionable advice.
You have access to the full PR diff and metadata provided in the message.
Format your response in GitHub Markdown."""

def handle_comment_command(pr_number, comment_body):
    question = comment_body.replace("/claude", "", 1).strip()
    if not question:
        question = "Summarize this PR and tell me what to verify before merging."

    pr   = get_pr_info(pr_number)
    diff = get_pr_diff(pr_number)
    if len(diff) > 40_000:
        diff = diff[:40_000] + "

[... diff truncated ...]"

    user_msg = f"""## PR Context
**Title:** {pr['title']}
**Author:** {pr['user']['login']}
**Branch:** `{pr['head']['ref']}` → `{pr['base']['ref']}`
**Description:** {pr.get('body') or '(none)'}

## Diff
```diff
{diff}
```

## Developer's Question
{question}"""

    answer = ask_claude(COMMAND_SYSTEM, user_msg)
    preview = question[:120] + ("..." if len(question) > 120 else "")
    full_response = (
        f"## 🤖 Claude

"
        f"> Replying to: *{preview}*

---

"
        f"{answer}

"
        f"---
*[{MODEL}](https://openrouter.ai) via OpenRouter*"
    )
    post_pr_comment(pr_number, full_response)
    print(f"✅ Replied to /claude command on PR #{pr_number}")

# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not PR_NUMBER:
        print("No PR_NUMBER set — exiting")
        sys.exit(0)

    pr_num = int(PR_NUMBER)

    if EVENT_NAME == "issue_comment" and COMMENT_BODY.strip().startswith("/claude"):
        handle_comment_command(pr_num, COMMENT_BODY)
    else:
        review_pr(pr_num)
