#!/usr/bin/env python3
"""
Claude PR Reviewer — runs inside GitHub Actions.
Fetches the PR diff, sends it to Claude, and posts a detailed review comment.
Also handles /claude commands in PR comments for on-demand responses.
"""

import os
import sys
import json
import httpx

# ── Config ────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GITHUB_TOKEN      = os.environ["GITHUB_TOKEN"]
REPO              = os.environ["GITHUB_REPOSITORY"]          # owner/repo
PR_NUMBER         = os.environ.get("PR_NUMBER", "")
EVENT_NAME        = os.environ.get("GITHUB_EVENT_NAME", "")
COMMENT_BODY      = os.environ.get("COMMENT_BODY", "")
CLAUDE_MODEL      = "claude-sonnet-4-6"

GH_API   = "https://api.github.com"
ANT_API  = "https://api.anthropic.com/v1/messages"

HEADERS_GH  = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
HEADERS_ANT = {"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"}

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
    """event: APPROVE | REQUEST_CHANGES | COMMENT"""
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

# ── Claude helper ──────────────────────────────────────────────────────────────
def ask_claude(system_prompt, user_message):
    payload = {
        "model": CLAUDE_MODEL,
        "max_tokens": 4096,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_message}],
    }
    r = httpx.post(ANT_API, headers=HEADERS_ANT, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()["content"][0]["text"]

# ── Review logic ───────────────────────────────────────────────────────────────
REVIEW_SYSTEM = """You are an expert code reviewer for the **Nexus** project — an LLM-powered knowledge retrieval platform built with FastAPI (Python) + Next.js (TypeScript) + FAISS + Neo4j.

Your job is to review pull requests with the following checks:

1. **Correctness** — bugs, off-by-one errors, incorrect logic
2. **Security** — injection risks, exposed secrets, auth bypasses, OWASP top 10
3. **Performance** — N+1 queries, blocking async calls, unnecessary re-renders
4. **Code Quality** — readability, naming, duplication, unnecessary complexity
5. **Tests** — are tests added/updated for the changed code?
6. **Breaking Changes** — API contract changes, DB schema changes without migrations

Format your review in GitHub Markdown with:
- A brief **Summary** (2–3 sentences)
- **Issues Found** (grouped as 🔴 Critical / 🟡 Warning / 🟢 Suggestion)
- **Verdict**: one of APPROVE ✅ | REQUEST_CHANGES ❌ | NEEDS_DISCUSSION 💬

Be direct and specific. Reference file paths and line numbers where possible.
If the diff is clean with no issues, say so confidently."""

def review_pr(pr_number):
    pr = get_pr_info(pr_number)
    diff = get_pr_diff(pr_number)
    head_sha = pr["head"]["sha"]

    # Truncate diff if too large (Claude has a context limit)
    if len(diff) > 80_000:
        diff = diff[:80_000] + "

[... diff truncated due to size ...]"

    user_msg = f"""## Pull Request: {pr['title']}

**Author:** {pr['user']['login']}
**Branch:** `{pr['head']['ref']}` → `{pr['base']['ref']}`
**Description:** {pr.get('body') or '(no description provided)'}
**Changed files:** {pr['changed_files']} | **Additions:** +{pr['additions']} | **Deletions:** -{pr['deletions']}
**Mergeable:** {pr.get('mergeable', 'unknown')} | **Conflicts:** {'YES ⚠️' if pr.get('mergeable') is False else 'None detected'}

---

## Diff

```diff
{diff}
```"""

    review_body = ask_claude(REVIEW_SYSTEM, user_msg)

    # Determine GitHub review event based on Claude's verdict
    event = "COMMENT"
    if "APPROVE ✅" in review_body or "Verdict**: APPROVE" in review_body:
        event = "APPROVE"
    elif "REQUEST_CHANGES ❌" in review_body or "Verdict**: REQUEST_CHANGES" in review_body:
        event = "REQUEST_CHANGES"

    # Add header to the review
    header = f"## 🤖 Claude Code Review

> Automated review by [Claude {CLAUDE_MODEL}](https://claude.ai/code) · [View workflow run](https://github.com/{REPO}/actions)

---

"
    full_review = header + review_body

    post_pr_review(pr_number, full_review, event)

    print(f"✅ Posted review with event={event} on PR #{pr_number}")

    # If approved and no conflicts, check whether CI passed and auto-merge
    if event == "APPROVE" and pr.get("mergeable") is not False:
        checks = get_check_runs(head_sha)
        failed = [c for c in checks if c["conclusion"] in ("failure", "timed_out") and c["name"] != "claude-review"]
        pending = [c for c in checks if c["status"] in ("queued", "in_progress") and c["name"] != "claude-review"]

        if failed:
            comment = f"⚠️ **Claude approved this PR** but the following CI checks are failing — please fix before merging:
" + \
                      "
".join(f"- `{c['name']}`: {c['conclusion']}" for c in failed)
            post_pr_comment(pr_number, comment)
        elif pending:
            post_pr_comment(pr_number, "⏳ **Claude approved this PR.** Waiting for other CI checks to complete before auto-merge is considered.")
        else:
            # All checks passed — auto-merge
            try:
                merge_pr(pr_number, f"{pr['title']} (#{pr_number})", head_sha)
                post_pr_comment(pr_number, f"🎉 **Auto-merged by Claude!** All checks passed and the code review was clean.

Squash-merged `{pr['head']['ref']}` → `{pr['base']['ref']}`.")
                print(f"✅ Auto-merged PR #{pr_number}")
            except Exception as e:
                post_pr_comment(pr_number, f"✅ **Claude approved this PR** but auto-merge failed (possibly needs maintainer merge):
```
{e}
```")

# ── Command handler (/claude ...) ──────────────────────────────────────────────
COMMAND_SYSTEM = """You are Claude, an AI assistant embedded in the GitHub PR workflow for the Nexus project.
A developer has sent you a command or question in a PR comment using `/claude`.
Answer helpfully and concisely. You have access to the PR context provided.
Format your response in GitHub Markdown. Keep it focused and actionable."""

def handle_comment_command(pr_number, comment_body):
    # Strip the /claude prefix
    question = comment_body.replace("/claude", "").strip()
    if not question:
        question = "Please summarize this PR and suggest what to check before merging."

    pr = get_pr_info(pr_number)
    diff = get_pr_diff(pr_number)
    if len(diff) > 40_000:
        diff = diff[:40_000] + "

[... diff truncated ...]"

    user_msg = f"""## PR Context
**Title:** {pr['title']}
**Author:** {pr['user']['login']}
**Branch:** `{pr['head']['ref']}` → `{pr['base']['ref']}`
**Description:** {pr.get('body') or '(none)'}

## Diff (truncated)
```diff
{diff}
```

## Developer's Question
{question}"""

    answer = ask_claude(COMMAND_SYSTEM, user_msg)
    full_response = f"## 🤖 Claude Response

> Replying to: *{question[:100]}{'...' if len(question) > 100 else ''}*

---

{answer}

---
*[Claude {CLAUDE_MODEL}](https://claude.ai/code)*"
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
