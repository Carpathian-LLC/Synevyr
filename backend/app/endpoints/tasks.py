# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# Path: app/endpoints/tasks.py
# ------------------------------------------------------------------------------------
# Notes:
# Kick off tasks early. Support:
#   1) Ingest-only
#   2) Clean-only
#   3) Ingest → Clean (one-click workflow, default)
#
# Scheduling:
#   - Celery Beat runs both every 6 hours.
#   - These routes let you run them early.
#
# Progress:
#   - Frontend polls /tasks/<task_id>/status (no Socket.IO).
#   - Ingest task emits PROGRESS via self.update_state(meta=...).
#   - Cleaner may report STARTED/SUCCESS unless you add update_state calls inside it.
# ------------------------------------------------------------------------------------

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import uuid4

from flask import Blueprint, jsonify, request, abort
from celery.result import AsyncResult
from celery.canvas import chain, Signature

from app.extensions import csrf, celery
from app.tasks.refresh_data_sources import update_data_sources_task
from app.tasks.clean_user_data import build_source_metrics_daily_task

# ------------------------------------------------------------------------------------
# Vars
tasks_bp = Blueprint("tasks_bp", __name__)

SIX_HOURS_SECONDS: int = 21600

# ------------------------------------------------------------------------------------
# Helpers

def _serialize_result(res: AsyncResult) -> Dict[str, Any]:
    """
    Return a consistent status payload for a single Celery task result.
    """
    info: Optional[Dict[str, Any]]
    try:
        info = res.info if isinstance(res.info, dict) else (
            {"message": str(res.info)} if res.info is not None else None
        )
    except Exception:
        info = None

    payload: Dict[str, Any] = {
        "task_id": res.id,
        "state": res.state,             # PENDING, STARTED, PROGRESS, RETRY, SUCCESS, FAILURE
        "ready": res.ready(),
        "successful": (res.successful() if res.ready() else None),
        "info": info,
    }
    return payload


def _apply_queue(sig: Signature, queue: Optional[str]) -> Signature:
    """
    Set a queue on a signature if provided, and return it for chaining.
    """
    return sig.set(queue=queue) if queue else sig


# ------------------------------------------------------------------------------------
# Routes

@tasks_bp.route("/tasks/run/update-data-sources", methods=["POST"])
@csrf.exempt
def run_update_data_sources_now():
    """
    Enqueue ingestion immediately. By default also chains the cleaner.

    Body (all optional):
    {
      "args": [...],
      "kwargs": {...},
      "queue_ingest": "ingest",
      "queue_clean": "etl",
      "chain_clean": true   // default true
    }

    Returns:
    {
      "workflow": "ingest_then_clean" | "ingest_only",
      "description": "Runs automatically every 6 hours; you started it early.",
      "ingest_task_id": "<uuid>",
      "clean_task_id": "<uuid or null>",
      "final_task_id": "<uuid of last task returned by Celery>"
    }
    """
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    args = payload.get("args", [])
    kwargs = payload.get("kwargs", {})
    queue_ingest: Optional[str] = payload.get("queue_ingest")
    queue_clean: Optional[str] = payload.get("queue_clean")
    chain_clean: bool = payload.get("chain_clean", True)

    # Pre-assign task IDs so frontend can poll both without guessing
    ingest_id: str = str(uuid4())
    ingest_sig: Signature = update_data_sources_task.s(*args, **kwargs).set(task_id=ingest_id)
    ingest_sig = _apply_queue(ingest_sig, queue_ingest)

    if chain_clean:
        clean_id: str = str(uuid4())
        clean_sig: Signature = build_source_metrics_daily_task.s().set(task_id=clean_id)
        clean_sig = _apply_queue(clean_sig, queue_clean)

        # Chain: ingest → clean
        result = chain(ingest_sig, clean_sig).apply_async()
        return jsonify({
            "workflow": "ingest_then_clean",
            "description": "Scheduled to run every 6 hours; you started ingestion and cleaning early.",
            "ingest_task_id": ingest_id,
            "clean_task_id": clean_id,
            "final_task_id": result.id   # this will be the last signature's id (clean_id)
        }), 202

    # Ingest only
    result = ingest_sig.apply_async()
    return jsonify({
        "workflow": "ingest_only",
        "description": "Scheduled to run every 6 hours; you started ingestion early.",
        "ingest_task_id": ingest_id,
        "clean_task_id": None,
        "final_task_id": result.id
    }), 202


@tasks_bp.route("/tasks/run/build-source-metrics", methods=["POST"])
@csrf.exempt
def run_build_source_metrics_now():
    """
    Enqueue cleaner immediately (no ingest).
    Optional body:
    { "queue_clean": "etl" }

    Returns:
    { "task_id": "<uuid>" }
    """
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    queue_clean: Optional[str] = payload.get("queue_clean")

    clean_id: str = str(uuid4())
    clean_sig: Signature = build_source_metrics_daily_task.s().set(task_id=clean_id)
    clean_sig = _apply_queue(clean_sig, queue_clean)
    res = clean_sig.apply_async()
    return jsonify({
        "task_id": res.id,
        "description": "Cleaner runs automatically every 6 hours; you started it early."
    }), 202


@tasks_bp.route("/tasks/<task_id>/status", methods=["GET"])
@csrf.exempt
def task_status(task_id: str):
    """
    Poll the status of a single task id (ingest OR clean).
    """
    res = AsyncResult(task_id, app=celery)
    return jsonify(_serialize_result(res)), 200


@tasks_bp.route("/tasks/<task_id>/result", methods=["GET"])
@csrf.exempt
def task_result(task_id: str):
    """
    Fetch the result payload of a finished task.
    409 if not ready.
    """
    res = AsyncResult(task_id, app=celery)
    if not res.ready():
        abort(409, description="Task not finished")
    return jsonify({
        "task_id": task_id,
        "state": res.state,
        "result": res.result
    }), 200


# ------------------------------------------------------------------------------------
# Optional: a convenience endpoint that starts the full workflow explicitly

@tasks_bp.route("/tasks/run/ingest-and-clean", methods=["POST"])
@csrf.exempt
def run_ingest_and_clean():
    """
    Explicit workflow route for clarity. Equivalent to /tasks/run/update-data-sources with chain_clean=true.

    Body (all optional):
    {
      "args": [...],
      "kwargs": {...},
      "queue_ingest": "ingest",
      "queue_clean": "etl"
    }
    """
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    args = payload.get("args", [])
    kwargs = payload.get("kwargs", {})
    queue_ingest: Optional[str] = payload.get("queue_ingest")
    queue_clean: Optional[str] = payload.get("queue_clean")

    ingest_id: str = str(uuid4())
    clean_id: str = str(uuid4())

    ingest_sig: Signature = update_data_sources_task.s(*args, **kwargs).set(task_id=ingest_id)
    clean_sig: Signature = build_source_metrics_daily_task.s().set(task_id=clean_id)

    ingest_sig = _apply_queue(ingest_sig, queue_ingest)
    clean_sig = _apply_queue(clean_sig, queue_clean)

    result = chain(ingest_sig, clean_sig).apply_async()
    return jsonify({
        "workflow": "ingest_then_clean",
        "description": "Scheduled to run every 6 hours; you started ingestion and cleaning early.",
        "ingest_task_id": ingest_id,
        "clean_task_id": clean_id,
        "final_task_id": result.id
    }), 202
