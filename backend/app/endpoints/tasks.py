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
#   2) Clean-only (v2 rollup from clean tables)
#   3) Ingest → Clean (one-click workflow, default)
#
# Scheduling:
#   - Celery Beat runs both every 6 hours.
#   - These routes let you run them early.
#
# Progress:
#   - Frontend polls /tasks/<task_id>/status (no Socket.IO).
#   - Ingest task emits PROGRESS via self.update_state(meta=...).
#   - Cleaner reports STARTED/SUCCESS/FAILURE; we return status consistently.
# ------------------------------------------------------------------------------------
from __future__ import annotations

from typing import Any, Dict, Optional, List, Tuple
from uuid import uuid4
from datetime import datetime

from flask import Blueprint, jsonify, request, abort
from celery.result import AsyncResult
from celery.canvas import chain, Signature

# Local Imports
from app.extensions import csrf, celery
from app.utils.logging import debug_logger
from app.tasks.extract_data_sources import extract_data_sources_task as extract_data_task
from app.tasks.transform_data import transform_data_task as transform_data_task
from app.tasks.load_analytics import load_analytics_task as load_analytics_task

# ------------------------------------------------------------------------------------
# Vars
tasks_bp = Blueprint("tasks_bp", __name__)

SIX_HOURS_SECONDS: int = 21600

# ------------------------------------------------------------------------------------
# Helpers

def _serialize_result(res: AsyncResult) -> Dict[str, Any]:
    """Return a consistent status payload for a single Celery task result."""
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
    """Set a queue on a signature if provided, and return it for chaining."""
    return sig.set(queue=queue) if queue else sig

def _parse_scope(payload: Dict[str, Any]) -> Tuple[bool, Optional[List[int]], Optional[str], Optional[str]]:
    """
    Extract and lightly validate scope controls for the cleaner.
    - force_reprocess: bool
    - user_ids: list[int] (optional)
    - since/until: 'YYYY-MM-DD' (optional)
    """
    force_reprocess: bool = bool(payload.get("force_reprocess", False))
    user_ids_raw = payload.get("user_ids")
    user_ids: Optional[List[int]] = None
    if isinstance(user_ids_raw, list):
        tmp: List[int] = []
        for v in user_ids_raw:
            try:
                tmp.append(int(v))
            except Exception:
                continue
        user_ids = tmp or None

    def _valid_date(s: Any) -> Optional[str]:
        if not isinstance(s, str):
            return None
        try:
            return datetime.fromisoformat(s).date().isoformat()
        except Exception:
            return None

    since: Optional[str] = _valid_date(payload.get("since"))
    until: Optional[str] = _valid_date(payload.get("until"))
    return force_reprocess, user_ids, since, until

# ------------------------------------------------------------------------------------
# Routes

@tasks_bp.route("/tasks/run/extract-data", methods=["POST"])
@csrf.exempt
def run_extract_data_now():
    """
    Extract raw data from connected sources into user_dataset_raw table.
    By default also chains the transform step.

    Body (all optional):
    {
      "args": [...],
      "kwargs": {...},          # forwarded to extract_data_task
      "queue_extract": "ingest",
      "queue_transform": "etl", 
      "chain_transform": true,  # default true

      // transform scope controls (forwarded when chain_transform=true)
      "force_reprocess": false,
      "user_ids": [1,2,3],
      "since": "2025-07-01",
      "until": "2025-08-31"
    }

    Returns:
    {
      "workflow": "extract_then_transform" | "extract_only",
      "description": "...",
      "extract_task_id": "<uuid>",
      "transform_task_id": "<uuid or null>",
      "final_task_id": "<uuid of last task in chain>"
    }
    """
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    args = payload.get("args", [])
    kwargs = payload.get("kwargs", {})
    queue_extract: Optional[str] = payload.get("queue_extract", payload.get("queue_ingest"))  # backward compat
    queue_transform: Optional[str] = payload.get("queue_transform", payload.get("queue_clean"))  # backward compat
    chain_transform: bool = payload.get("chain_transform", payload.get("chain_clean", True))  # backward compat

    force_reprocess, user_ids, since, until = _parse_scope(payload)

    # Pre-assign task IDs so frontend can poll both deterministically
    extract_id: str = str(uuid4())
    extract_sig: Signature = extract_data_task.s(*args, **kwargs).set(task_id=extract_id)
    extract_sig = _apply_queue(extract_sig, queue_extract)

    if chain_transform:
        transform_id: str = str(uuid4())
        transform_sig_kwargs: Dict[str, Any] = {
            "force_reprocess": force_reprocess,
            "user_ids": user_ids,
            "since": since,
            "until": until,
            "create_tables": True,
        }
        transform_sig: Signature = transform_data_task.s(**transform_sig_kwargs).set(task_id=transform_id)
        transform_sig = _apply_queue(transform_sig, queue_transform)

        debug_logger.info(f"[tasks] chaining extract({extract_id}) -> transform({transform_id})")
        result = chain(extract_sig, transform_sig).apply_async()
        return jsonify({
            "workflow": "extract_then_transform",
            "description": "Extract raw data then transform into clean staging tables.",
            "extract_task_id": extract_id,
            "transform_task_id": transform_id,
            "final_task_id": result.id
        }), 202

    debug_logger.info(f"[tasks] enqueue extract_only({extract_id})")
    result = extract_sig.apply_async()
    return jsonify({
        "workflow": "extract_only",
        "description": "Extract raw data from connected sources only.",
        "extract_task_id": extract_id,
        "transform_task_id": None,
        "final_task_id": result.id
    }), 202


@tasks_bp.route("/tasks/run/transform-data", methods=["POST"])
@csrf.exempt
def run_transform_data_now():
    """
    Transform raw data from user_dataset_raw into clean staging tables:
    leads_clean, customers_clean, orders_clean

    Body (all optional):
    {
        "queue_transform": "etl",
        "force_reprocess": true,
        "user_ids": [1,2,3],
        "since": "2025-07-01",
        "until": "2025-08-31"
    }

    Returns: { "task_id": "<uuid>", "description": "..." }
    """
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    queue_transform: Optional[str] = payload.get("queue_transform", payload.get("queue_clean"))  # backward compat
    force_reprocess, user_ids, since, until = _parse_scope(payload)

    transform_id: str = str(uuid4())
    transform_sig: Signature = transform_data_task.s(
        force_reprocess=force_reprocess,
        user_ids=user_ids,
        since=since,
        until=until,
        create_tables=True,
    ).set(task_id=transform_id)
    transform_sig = _apply_queue(transform_sig, queue_transform)

    debug_logger.info(f"[tasks] enqueue transform_data({transform_id})")
    res = transform_sig.apply_async()

    if force_reprocess and (since or until or user_ids):
        scope_bits = []
        if user_ids:
            scope_bits.append(f"user_ids={user_ids}")
        if since:
            scope_bits.append(f"since={since}")
        if until:
            scope_bits.append(f"until={until}")
        scope = "; ".join(scope_bits) if scope_bits else "all"
        description = f"Transform raw data to clean staging tables with scope: {scope}."
    elif force_reprocess:
        description = "Transform all raw data from beginning into clean staging tables."
    else:
        description = "Transform new raw data since last run into clean staging tables."

    return jsonify({"task_id": res.id, "description": description}), 202


@tasks_bp.route("/tasks/run/load-analytics", methods=["POST"])
@csrf.exempt
def run_load_analytics_now():
    """
    Load analytics data from clean staging tables into source_metrics_daily table.
    This is the final step that creates the analytics used by dashboards.
    """
    payload = request.get_json(silent=True) or {}
    queue_analytics = payload.get("queue_analytics", payload.get("queue_clean"))  # backward compat
    kwargs = {
        "force_reprocess": bool(payload.get("force_reprocess", False)),
        "user_ids": payload.get("user_ids"),
        "since": payload.get("since"),
        "until": payload.get("until"),
        "create_table": payload.get("create_table", True),
    }
    analytics_id = str(uuid4())
    sig = load_analytics_task.s(**kwargs).set(task_id=analytics_id)
    if queue_analytics:
        sig = sig.set(queue=queue_analytics)

    debug_logger.info(f"[tasks] enqueue load_analytics({analytics_id})")
    res = sig.apply_async()
    return jsonify({"task_id": res.id, "description": "Load analytics from clean staging tables"}), 202



@tasks_bp.route("/tasks/<task_id>/status", methods=["GET"])
@csrf.exempt
def task_status(task_id: str):
    """Poll the status of a single task id (ingest OR clean)."""
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


@tasks_bp.route("/tasks/run/extract-transform-load", methods=["POST"])
@csrf.exempt
def run_extract_transform_load():
    """
    Complete ETL workflow: Extract raw data, Transform to clean staging tables, Load analytics.
    Chains all three ETL steps in sequence.
    
    Body (all optional):
    {
      "args": [...],
      "kwargs": {...},                 // forwarded to extract task
      "queue_extract": "ingest",
      "queue_transform": "etl",
      "queue_load": "analytics",
      
      // transform and load scope controls
      "force_reprocess": false,
      "user_ids": [1,2,3],
      "since": "2025-07-01", 
      "until": "2025-08-31"
    }
    
    Returns:
    {
      "workflow": "extract_transform_load",
      "description": "...",
      "extract_task_id": "<uuid>",
      "transform_task_id": "<uuid>", 
      "load_task_id": "<uuid>",
      "final_task_id": "<uuid of last task in chain>"
    }
    """
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    args = payload.get("args", [])
    kwargs = payload.get("kwargs", {})
    queue_extract: Optional[str] = payload.get("queue_extract", payload.get("queue_ingest"))  # backward compat
    queue_transform: Optional[str] = payload.get("queue_transform", payload.get("queue_clean"))  # backward compat
    queue_load: Optional[str] = payload.get("queue_load", payload.get("queue_analytics"))  # backward compat

    force_reprocess, user_ids, since, until = _parse_scope(payload)

    # Pre-assign task IDs for deterministic polling
    extract_id: str = str(uuid4())
    transform_id: str = str(uuid4()) 
    load_id: str = str(uuid4())

    # Extract signature
    extract_sig: Signature = extract_data_task.s(*args, **kwargs).set(task_id=extract_id)
    extract_sig = _apply_queue(extract_sig, queue_extract)

    # Transform signature 
    transform_sig_kwargs: Dict[str, Any] = {
        "force_reprocess": force_reprocess,
        "user_ids": user_ids,
        "since": since,
        "until": until,
        "create_tables": True,
    }
    transform_sig: Signature = transform_data_task.s(**transform_sig_kwargs).set(task_id=transform_id)
    transform_sig = _apply_queue(transform_sig, queue_transform)

    # Load signature
    load_sig_kwargs: Dict[str, Any] = {
        "force_reprocess": force_reprocess,
        "user_ids": user_ids,
        "since": since,
        "until": until,
        "create_table": True,
    }
    load_sig: Signature = load_analytics_task.s(**load_sig_kwargs).set(task_id=load_id)
    load_sig = _apply_queue(load_sig, queue_load)

    debug_logger.info(f"[tasks] chaining extract({extract_id}) -> transform({transform_id}) -> load({load_id})")
    result = chain(extract_sig, transform_sig, load_sig).apply_async()
    return jsonify({
        "workflow": "extract_transform_load",
        "description": "Complete ETL pipeline: Extract raw data, Transform to clean staging, Load analytics.",
        "extract_task_id": extract_id,
        "transform_task_id": transform_id,
        "load_task_id": load_id,
        "final_task_id": result.id
    }), 202
