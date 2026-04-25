#!/usr/bin/env python3
"""
Claude PR Reviewer (OpenRouter) — full autonomous review, conflict detection,
codebase integration checks, and auto-merge on clean approval.
"""

import os, sys, json, httpx

OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
GITHUB_TOKEN       = os.environ["GITHUB_TOKEN"]
REPO               = os.environ["GITHUB_REPOSITORY"]
PR_NUMBER          = os.environ.get("PR_NUMBER", "")
EVENT_NAME         = os.environ.get("GITHUB_EVENT_NAME", "")
COMMENT_BODY       = os.environ.get("COMMENT_BODY", "")

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
    "X-Title": "Nexus PR Reviewer",
}

# ── GitHub helpers ─────────────────────────────────────────────────────────────

def gh(method, path, **kwargs):
    r = getattr(httpx, method)(f"{GH_API}{path}", headers=HEADERS_GH, timeout=30, **kwargs)
    r.raise_for_status()
    return r.json()

def get_pr_diff(pr_number):
    h = {**HEADERS_GH, "Accept": "application/vnd.github.v3.diff"}
    r = httpx.get(f"{GH_API}/repos/{REPO}/pulls/{pr_number}", headers=h, timeout=30)
    r.raise_for_status()
    return r.text

def get_pr_files(pr_number):
    """Returns list of changed files with patch info."""
    return gh("get", f"/repos/{REPO}/pulls/{pr_number}/files")

def get_file_content(path, ref="main"):
    """Fetch the current content of a file from the base branch."""
    try:
        import base64
        data = gh("get", f"/repos/{REPO}/contents/{path}?ref={ref}")
        return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    except Exception:
        return None

def get_pr_info(pr_number):
    return gh("get", f"/repos/{REPO}/pulls/{pr_number}")

def get_check_runs(sha):
    return gh("get", f"/repos/{REPO}/commits/{sha}/check-runs").get("check_runs", [])

def post_comment(pr_number, body):
    gh("post", f"/repos/{REPO}/issues/{pr_number}/comments", json={"body": body})

def post_review(pr_number, body, event="COMMENT", comments=None):
    payload = {"body": body, "event": event}
    if comments:
        payload["comments"] = comments
    gh("post", f"/repos/{REPO}/pulls/{pr_number}/reviews", json=payload)

def request_changes_inline(pr_number, body, inline_comments):
    """Post a REQUEST_CHANGES review with inline comments on specific lines."""
    post_review(pr_number, body, event="REQUEST_CHANGES", comments=inline_comments)

def merge_pr(pr_number, title, sha):
    gh("put", f"/repos/{REPO}/pulls/{pr_number}/merge", json={
        "commit_title": title,
        "sha": sha,
        "merge_method": "squash",
    })

def post_ai_unavailable(pr_number, action, error):
    post_comment(
        pr_number,
        "## 🤖 Claude Automation Unavailable\n\n"
        f"Claude could not {action} because the OpenRouter request failed:\n\n"
        f"```\n{type(error).__name__}: {str(error)[:500]}\n```\n\n"
        "This is an external AI service failure, so the workflow is not blocking the PR."
    )

# ── OpenRouter / Claude ────────────────────────────────────────────────────────

def ask_claude(system_prompt, user_message, max_tokens=6000):
    payload = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
    }
    r = httpx.post(OPENROUTER_URL, headers=HEADERS_OR, json=payload, timeout=180)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

# ── Codebase context builder ───────────────────────────────────────────────────

# Key files that give Claude context about the project's patterns and conventions
CONTEXT_FILES = [
    "backend/app/main.py",
    "backend/requirements.txt",
    "backend/app/core/config.py",
    "frontend/package.json",
    "frontend/src/app/layout.tsx",
    "docker-compose.yml",
    ".env.example",
]

def build_codebase_context(changed_files):
    """
    Fetch key existing files so Claude understands conventions,
    plus the current version of any file being modified.
    """
    context_parts = []

    # Always include key reference files
    for path in CONTEXT_FILES:
        content = get_file_content(path)
        if content:
            context_parts.append(f"### {path} (existing)\n```\n{content[:3000]}\n```")

    # Include current (pre-PR) version of every modified file
    for f in changed_files:
        filename = f["filename"]
        if filename not in CONTEXT_FILES and f["status"] in ("modified", "renamed"):
            content = get_file_content(filename)
            if content:
                snippet = content[:4000]
                context_parts.append(
                    f"### {filename} (CURRENT version before this PR)\n```\n{snippet}\n```"
                )

    return "\n\n".join(context_parts)

# ── Review prompt ──────────────────────────────────────────────────────────────

REVIEW_SYSTEM = """You are the **autonomous code guardian** for **Nexus** — an LLM-powered knowledge retrieval platform (FastAPI + Next.js + FAISS + Neo4j + Celery).

You have two responsibilities:
1. **Protect the codebase** — catch bugs, security holes, and integration breaks BEFORE they merge
2. **Help contributors improve** — give exact, copy-pasteable fixes so they know exactly what to change

---

## Your Review Process

### Step 1 — Understand the PR
Read the title, description, and diff. What is the contributor trying to do?

### Step 2 — Check for Errors
- **Runtime errors**: unhandled exceptions, wrong types, missing null checks, async/await misuse
- **Logic errors**: wrong conditions, off-by-one, incorrect data transformations
- **Import errors**: missing imports, circular imports, version mismatches with requirements.txt
- **Type errors**: TypeScript type violations, Pydantic model mismatches

### Step 3 — Integration Check (CRITICAL)
Compare the PR's changes against the existing codebase context provided:
- Does it follow the same patterns as existing code? (e.g., how routes are registered, how services are called)
- Does it break any existing API contracts? (changed endpoint paths, response schemas, removed fields)
- Does it conflict with existing DB models or migrations?
- Does it introduce duplicate functionality that already exists elsewhere?
- Are new dependencies added to requirements.txt / package.json?
- Does it respect the existing CORS, auth middleware, and error handling patterns?

### Step 4 — Security Scan
- Hardcoded secrets or API keys
- SQL injection, path traversal, XSS risks
- Unprotected endpoints (missing auth dependency)
- Insecure file handling (unrestricted upload types/sizes)

### Step 5 — Code Quality
- Naming consistency with existing code
- Unnecessary complexity or duplication
- Missing error handling for external calls (OpenAI, Neo4j, FAISS)

### Step 6 — Tests
- Are tests added for new functionality?
- Do existing tests still make sense given the changes?

---

## Output Format (GitHub Markdown)

## 🔍 PR Summary
(What this PR does — 2-3 sentences)

## ✅ What's Good
(Acknowledge correct, well-written parts)

## 🔴 Errors — Must Fix Before Merge
For EACH error, provide:
**File:** `path/to/file.py` line X
**Problem:** What is wrong and why it will fail
**Fix:**
```python
# exact replacement code here
```

## 🟡 Integration Issues — Should Fix
For EACH issue, provide:
**File:** `path/to/file.py`
**Problem:** How this conflicts with or diverges from the existing codebase
**Fix:**
```python
# exact replacement code here
```

## 🟢 Suggestions — Optional Improvements
(Nice-to-haves, style, performance. Provide code snippets.)

## 🏁 Verdict
**APPROVE ✅** — No errors, integrates cleanly, ready to merge
**REQUEST_CHANGES ❌** — Has errors or integration issues (listed above)
**NEEDS_DISCUSSION 💬** — Architecture question that needs team input

(One sentence justifying the verdict)

---

IMPORTANT: Be specific. Never say "consider improving X" without showing the exact code change.
If a file cannot be reviewed because it's truncated, say so explicitly."""

def review_pr(pr_number):
    pr           = get_pr_info(pr_number)
    diff         = get_pr_diff(pr_number)
    changed_files = get_pr_files(pr_number)
    head_sha     = pr["head"]["sha"]
    base_ref     = pr["base"]["ref"]

    print(f"📋 PR #{pr_number}: {pr['title']}")
    print(f"   Files changed: {len(changed_files)} | +{pr['additions']} -{pr['deletions']}")

    # Build codebase context (existing files for integration checking)
    print("📂 Fetching codebase context...")
    codebase_ctx = build_codebase_context(changed_files)

    # Truncate diff if huge
    if len(diff) > 70_000:
        diff = diff[:70_000] + "\n\n[... diff truncated — review remaining files manually ...]"

    # Conflict detection
    mergeable    = pr.get("mergeable")
    conflict_msg = ""
    if mergeable is False:
        conflict_msg = (
            "\n\n> ⚠️ **MERGE CONFLICT DETECTED** — "
            "this PR cannot be merged until conflicts are resolved."
        )

    user_msg = f"""## Pull Request #{pr_number}: {pr['title']}

**Author:** @{pr['user']['login']}
**Branch:** `{pr['head']['ref']}` → `{base_ref}`
**Description:**
{pr.get('body') or '*(no description provided)*'}

**Stats:** {pr['changed_files']} files · +{pr['additions']} additions · -{pr['deletions']} deletions
**Merge status:** {'⚠️ CONFLICTS DETECTED' if mergeable is False else '✅ No conflicts'}

---

## Existing Codebase Context
(Use this to check integration — these are the CURRENT files before this PR)

{codebase_ctx}

---

## PR Diff (what the contributor changed)

```diff
{diff}
```"""

    print("🤖 Asking Claude to review...")
    try:
        review_body = ask_claude(REVIEW_SYSTEM, user_msg)
    except Exception as e:
        print(f"⚠️ Claude review unavailable: {e}")
        post_ai_unavailable(pr_number, "review this PR", e)
        return

    # Determine event
    event = "COMMENT"
    if "APPROVE ✅" in review_body or "**APPROVE" in review_body:
        event = "APPROVE"
    elif "REQUEST_CHANGES ❌" in review_body or "**REQUEST_CHANGES" in review_body:
        event = "REQUEST_CHANGES"

    header = (
        f"## 🤖 Claude Code Review{conflict_msg}\n\n"
        f"> **Model:** [{MODEL}](https://openrouter.ai) · "
        f"**PR:** #{pr_number} · "
        f"[Workflow run](https://github.com/{REPO}/actions)\n\n"
        f"---\n\n"
    )

    post_review(pr_number, header + review_body, event)
    print(f"✅ Posted review (event={event})")

    # If there are merge conflicts, post a dedicated comment explaining how to fix
    if mergeable is False:
        conflict_help = (
            "## ⚠️ Merge Conflicts Need to Be Resolved\n\n"
            "Your branch has conflicts with `main`. Here's how to fix them:\n\n"
            "```bash\n"
            f"git checkout {pr['head']['ref']}\n"
            "git fetch origin\n"
            f"git rebase origin/{base_ref}\n"
            "# resolve any conflicts in your editor\n"
            "git add .\n"
            "git rebase --continue\n"
            "git push --force-with-lease\n"
            "```\n\n"
            "Once conflicts are resolved and you push, Claude will re-review automatically."
        )
        post_comment(pr_number, conflict_help)
        print("⚠️ Posted conflict resolution instructions")
        return

    # Auto-merge if approved
    if event == "APPROVE":
        checks  = get_check_runs(head_sha)
        failed  = [c for c in checks if c["conclusion"] in ("failure", "timed_out")  and "claude" not in c["name"].lower()]
        pending = [c for c in checks if c["status"]    in ("queued", "in_progress") and "claude" not in c["name"].lower()]

        if failed:
            lines = "\n".join(
                f"- `{c['name']}`: {c['conclusion']} — [view]({c['html_url']})"
                for c in failed
            )
            post_comment(
                pr_number,
                "## ✅ Claude Approved — But CI Is Failing\n\n"
                "The code review passed but these checks need to be fixed before merge:\n\n"
                f"{lines}\n\n"
                "Fix the failures, push, and Claude will re-review and auto-merge once everything is green."
            )
            print("⚠️ Approved but CI failing — posted CI failure comment")
        elif pending:
            post_comment(
                pr_number,
                "## ✅ Claude Approved — Waiting for CI\n\n"
                "The code review passed. Waiting for other CI checks to finish.\n"
                "Claude will auto-merge once all checks are green."
            )
            print("⏳ Approved, CI pending")
        else:
            # All clear — merge it
            try:
                merge_pr(pr_number, f"{pr['title']} (#{pr_number})", head_sha)
                post_comment(
                    pr_number,
                    "## 🎉 Merged by Claude!\n\n"
                    f"Code review passed, all CI checks green — squash-merged into `{base_ref}`.\n\n"
                    f"Thanks for the contribution, @{pr['user']['login']}! 🙌"
                )
                print(f"🎉 Auto-merged PR #{pr_number}")
            except Exception as e:
                post_comment(
                    pr_number,
                    "## ✅ Claude Approved\n\n"
                    "Review passed but auto-merge failed (repo may require maintainer approval):\n"
                    f"```\n{e}\n```\n"
                    "A maintainer can merge manually."
                )

# ── /claude command handler ────────────────────────────────────────────────────

COMMAND_SYSTEM = """You are Claude, the AI code assistant for the Nexus LLM knowledge retrieval platform.
A developer has asked you a question directly in a PR comment using `/claude`.

You have the full PR diff and codebase context. Answer with:
- Concrete, actionable advice
- Exact code snippets when suggesting changes
- Short explanation of *why* you're recommending something

Be direct. Don't hedge. If something is wrong, say so clearly.
Format in GitHub Markdown."""

def handle_comment_command(pr_number, comment_body):
    question = comment_body.replace("/claude", "", 1).strip()
    if not question:
        question = "Review this PR thoroughly. What should I check or fix before it can be merged?"

    pr            = get_pr_info(pr_number)
    diff          = get_pr_diff(pr_number)
    changed_files = get_pr_files(pr_number)

    if len(diff) > 40_000:
        diff = diff[:40_000] + "\n\n[... diff truncated ...]"

    codebase_ctx = build_codebase_context(changed_files)

    user_msg = f"""## PR Context
**Title:** {pr['title']}
**Author:** @{pr['user']['login']}
**Branch:** `{pr['head']['ref']}` → `{pr['base']['ref']}`
**Description:** {pr.get('body') or '(none)'}

## Existing Codebase Context
{codebase_ctx}

## PR Diff
```diff
{diff}
```

## Developer's Question
{question}"""

    try:
        answer = ask_claude(COMMAND_SYSTEM, user_msg)
    except Exception as e:
        print(f"⚠️ Claude reply unavailable: {e}")
        post_ai_unavailable(pr_number, "answer this /claude request", e)
        return
    preview = question[:120] + ("..." if len(question) > 120 else "")
    post_comment(
        pr_number,
        f"## 🤖 Claude\n\n> *{preview}*\n\n---\n\n{answer}\n\n"
        f"---\n*[{MODEL}](https://openrouter.ai) via OpenRouter · "
        f"Reply with `/claude <question>` for follow-ups*"
    )
    print(f"✅ Replied to /claude on PR #{pr_number}")

# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not PR_NUMBER:
        print("No PR_NUMBER — exiting")
        sys.exit(0)

    pr_num = int(PR_NUMBER)

    if EVENT_NAME == "issue_comment" and COMMENT_BODY.strip().startswith("/claude"):
        handle_comment_command(pr_num, COMMENT_BODY)
    else:
        review_pr(pr_num)
