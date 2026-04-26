import asyncio
import hashlib
import hmac
import json
import logging
import shutil
import subprocess
import uuid

from fastapi import BackgroundTasks, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from pydantic import BaseModel

from config import (
    ARTIFACT_CHAR_LIMIT, BASE_BRANCH, BASE_WORKSPACE,
    BOT_COMMENT_PREFIX, BOT_MENTION, BOT_USERNAME,
    DEFAULT_LLM_PROVIDER, ENABLE_TEST_ENDPOINTS, MAX_READ_FILES,
    REPO_NAME, REPO_OWNER, WEBHOOK_SECRET,
)
from git_utils import github_api_request, run_git
from job_store import create_job, update_job
from llm import create_models, sync_generate_and_parse
from models import DeliveryPlan, FileRequest, ReviewResult
from workspace import (
    get_repo_summary, read_agent_files,
    validate_files, write_files,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Webhook endpoint ──────────────────────────────────────────────────────────

@router.post("/github-webhook")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str = Header(None),
    x_github_event: str = Header(None),
):
    payload_bytes = await request.body()

    # Validate webhook HMAC signature
    if not x_hub_signature_256:
        raise HTTPException(status_code=401, detail="Missing signature")
    expected_mac = hmac.new(
        WEBHOOK_SECRET.encode(), payload_bytes, hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(f"sha256={expected_mac}", x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")

    if x_github_event != "issue_comment":
        return {"status": "ignored_event"}

    payload = json.loads(payload_bytes)
    if payload.get("action") != "created":
        return {"status": "ignored_action"}
    if "pull_request" not in payload.get("issue", {}):
        return {"status": "ignored_not_pr"}

    comment_body = payload["comment"]["body"]
    commenter    = payload["comment"]["user"]["login"]
    pr_api_url   = payload["issue"]["pull_request"]["url"]
    comments_url = payload["issue"]["comments_url"]

    # Prevent infinite loops — ignore our own comments
    if commenter == BOT_USERNAME or comment_body.startswith(BOT_COMMENT_PREFIX):
        return {"status": "ignored_bot"}
    if BOT_MENTION not in comment_body:
        return {"status": "ignored_not_addressed"}

    job_id = uuid.uuid4().hex[:12]
    background_tasks.add_task(
        _dispatch_pr_revision,
        pr_api_url, comments_url, comment_body, job_id, None,
    )
    return JSONResponse(
        status_code=202,
        content={"status": "accepted", "job_id": job_id},
    )


# ── Test endpoint (dev only) ──────────────────────────────────────────────────

class TestWebhookRequest(BaseModel):
    pr_number: int
    comment_body: str
    parent_job_id: str | None = None


@router.post("/test-webhook")
async def test_webhook(
    body: TestWebhookRequest,
    background_tasks: BackgroundTasks,
):
    """Bypass HMAC — directly trigger PR revision. Gated by ENABLE_TEST_ENDPOINTS."""
    if not ENABLE_TEST_ENDPOINTS:
        raise HTTPException(status_code=403, detail="Test endpoints are disabled")

    pr_api_url = (
        f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
        f"/pulls/{body.pr_number}"
    )
    comments_url = (
        f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
        f"/issues/{body.pr_number}/comments"
    )
    job_id = uuid.uuid4().hex[:12]
    background_tasks.add_task(
        _dispatch_pr_revision,
        pr_api_url, comments_url, body.comment_body, job_id, body.parent_job_id,
    )
    return JSONResponse(
        status_code=202,
        content={"status": "accepted", "job_id": job_id},
    )


# ── Revision pipeline ─────────────────────────────────────────────────────────

async def _dispatch_pr_revision(
    pr_api_url: str,
    comments_url: str,
    comment_body: str,
    job_id: str,
    parent_job_id: str | None = None,
):
    """Async entry point — offloads blocking work to a thread."""
    await asyncio.to_thread(
        _sync_pr_revision, pr_api_url, comments_url, comment_body,
        job_id, parent_job_id,
    )


def _sync_pr_revision(
    pr_api_url: str,
    comments_url: str,
    comment_body: str,
    job_id: str,
    parent_job_id: str | None = None,
):
    """Synchronous revision pipeline — runs entirely off the event loop."""
    # ── Track revision as a linked job ────────────────────────────────────
    create_job(job_id, goal=f"Revision: {comment_body[:120]}")
    update_job(
        job_id,
        job_type="revision",
        parent_job_id=parent_job_id,
        status="running",
        current_step="cloning",
    )

    job_workspace = BASE_WORKSPACE / f"fix-{job_id}"
    _, _, rev_reviewer, rev_fixer = create_models(DEFAULT_LLM_PROVIDER)

    try:
        github_api_request("POST", comments_url, {
            "body": (
                f"\U0001f916 **Revision Acknowledged.** Investigating... "
                f"(Job: `{job_id}`)"
            ),
        })

        pr_data     = github_api_request("GET", pr_api_url)
        branch_name = pr_data["head"]["ref"]
        repo_url    = f"https://github.com/{REPO_OWNER}/{REPO_NAME}.git"
        run_git("clone", "--branch", branch_name, "--depth", "1",
                repo_url, str(job_workspace))
        run_git("config", "user.email", "orchestrator@automated.dev",
                cwd=str(job_workspace), timeout=10)
        run_git("config", "user.name", "SDLC Orchestrator",
                cwd=str(job_workspace), timeout=10)

        # Get PR diff for context (may fail on shallow clone)
        pr_diff = ""
        try:
            run_git("fetch", "origin", BASE_BRANCH, "--depth", "1",
                    cwd=str(job_workspace), timeout=60)
            diff_result = run_git("diff", "FETCH_HEAD..HEAD",
                                  cwd=str(job_workspace), timeout=30)
            pr_diff = diff_result.stdout[:ARTIFACT_CHAR_LIMIT]
        except subprocess.CalledProcessError:
            logger.warning(f"Job {job_id}: Could not compute PR diff (shallow clone)")

        # Investigation: which files does the fixer need?
        update_job(job_id, current_step="investigating")
        repo_tree  = get_repo_summary(job_workspace, max_chars=3000)
        file_req   = sync_generate_and_parse(
            rev_fixer,
            f"User commented on a PR: '{comment_body}'\n"
            f"PR diff against {BASE_BRANCH}:\n{pr_diff}\n"
            f"Repo file tree:\n{repo_tree}\n"
            f"Which files (max {MAX_READ_FILES}) do you need to address "
            f"this comment? Return a JSON with 'files_to_read' (array of file paths).",
            FileRequest,
            {},
        )

        update_job(job_id, current_step="fixing")
        file_context  = read_agent_files(file_req.files_to_read, job_workspace)
        delivery = sync_generate_and_parse(
            rev_fixer,
            f"User Comment: '{comment_body}'\n"
            f"PR diff against {BASE_BRANCH}:\n{pr_diff}\n"
            f"Existing Files:\n{json.dumps(file_context)}\n"
            f"Fix ONLY what the user asked for. Do not revert other changes.\n"
            f"Return a JSON DeliveryPlan with 'files' (array of {{path, content}}), "
            f"'commit_message', and 'pr_title'.",
            DeliveryPlan,
            {},
        )

        # Review gate
        update_job(job_id, current_step="reviewing")
        review = sync_generate_and_parse(
            rev_reviewer,
            f"Review this fix against the user comment: '{comment_body}'\n"
            f"Files to commit:\n"
            + json.dumps({
                "comment": comment_body,
                "files": [
                    {"path": f.path, "content": f.content[:ARTIFACT_CHAR_LIMIT]}
                    for f in delivery.files
                ],
            }, indent=2)
            + f"\nIs this fix correct and minimal? Return a JSON with 'approved' (boolean) "
              f"and 'issues' (array of strings).",
            ReviewResult,
            {},
        )

        if not review.approved:
            github_api_request("POST", comments_url, {
                "body": (
                    f"\U0001f916 Generated a fix but the reviewer rejected it:\n"
                    f"- " + "\n- ".join(review.issues)
                    + "\n\nPlease provide more specific guidance."
                ),
            })
            update_job(
                job_id, status="complete", current_step="done",
                result="Reviewer rejected the fix: " + "; ".join(review.issues),
            )
            return

        if not delivery.files:
            github_api_request("POST", comments_url, {
                "body": (
                    "\U0001f916 Analyzed the comment but determined no "
                    "file changes are needed."
                ),
            })
            update_job(
                job_id, status="complete", current_step="done",
                result="No file changes needed.",
            )
            return

        update_job(job_id, current_step="pushing")
        validate_files(delivery.files, job_workspace)
        write_files(delivery.files, job_workspace)
        run_git("add", ".", cwd=str(job_workspace), timeout=30)

        diff = run_git("diff", "--cached", "--stat", cwd=str(job_workspace), timeout=30)
        if not diff.stdout.strip():
            github_api_request("POST", comments_url, {
                "body": (
                    "\U0001f916 Code analysis complete, but no net changes "
                    "were produced."
                ),
            })
            update_job(
                job_id, status="complete", current_step="done",
                result="No net changes produced.",
            )
            return

        run_git("commit", "-m", delivery.commit_message, cwd=str(job_workspace), timeout=30)
        run_git("push", "origin", branch_name, cwd=str(job_workspace), timeout=120)

        github_api_request("POST", comments_url, {
            "body": (
                f"\U0001f916 **Revision Complete.** Pushed fix: "
                f"`{delivery.commit_message}`"
            ),
        })
        update_job(
            job_id, status="complete", current_step="done",
            result=f"Pushed fix: {delivery.commit_message}",
        )

    except Exception as exc:
        logger.exception(f"Revision Job {job_id} failed")
        update_job(
            job_id, status="failed", current_step="error",
            error=f"Revision failed: {type(exc).__name__}: {exc}",
        )
        try:
            github_api_request("POST", comments_url, {
                "body": (
                    f"\U0001f6d1 **Revision Failed.** Check container logs "
                    f"for Job `{job_id}`."
                ),
            })
        except Exception:
            logger.error(f"Job {job_id}: Also failed to post failure notification.")
    finally:
        if job_workspace.exists():
            shutil.rmtree(job_workspace, ignore_errors=True)
