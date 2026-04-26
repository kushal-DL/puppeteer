import asyncio
import json
import logging

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from fastapi.routing import APIRouter

from job_store import get_job, list_jobs

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/api/jobs")
async def get_all_jobs():
    """Return summary list of all tracked jobs (for dashboard)."""
    return list_jobs()


@router.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """Poll endpoint for async job progress."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/stream/{job_id}")
async def stream_job_events(job_id: str):
    """Server-Sent Events stream for real-time DAG progress.

    Emits one SSE message per event:
      agent_started, agent_done, agent_failed, agent_pruned, helper_spawned.
    Closes automatically when the job reaches a terminal state.

    PowerShell true-streaming loop:
        $req = [System.Net.WebRequest]::Create('http://<host>/stream/<job_id>')
        $stream = $req.GetResponse().GetResponseStream()
        $reader = [System.IO.StreamReader]::new($stream)
        while (-not $reader.EndOfStream) { Write-Host $reader.ReadLine() }
    """
    async def _sse():
        cursor = 0
        while True:
            job = get_job(job_id)
            if not job:
                yield 'event: error\ndata: {"detail": "job not found"}\n\n'
                return
            for ev in job["events"][cursor:]:
                yield f"event: {ev['type']}\ndata: {json.dumps(ev)}\n\n"
            cursor = len(job["events"])
            if job["status"] in ("complete", "failed"):
                terminal = {
                    "status": job["status"],
                    "result": job.get("result"),
                    "error": job.get("error"),
                }
                yield f"event: done\ndata: {json.dumps(terminal)}\n\n"
                return
            await asyncio.sleep(0.4)

    return StreamingResponse(
        _sse(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
