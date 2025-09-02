# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# Notes:
# User data ingestion task - fetches data from connected API sources
# This is step 1 of the user data pipeline: API → user_dataset_raw → source_metrics_daily
# Scheduling:
#   - This task is scheduled by Celery Beat to run automatically every 6 hours.
#   - You can also kick it off early via the POST /tasks/run/update-data-sources route.
# Progress:
#   - Frontend can poll /tasks/<task_id>/status to read self.update_state(meta=...) progress.
# ------------------------------------------------------------------------------------

from datetime import datetime
import hashlib
import json
from typing import Any, Dict, List
import requests
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from sqlalchemy.dialects.mysql import insert as mysql_insert

from app.extensions import celery, db
from app.models.data_sources import DataSource, UserDatasetRaw
from app.utils.logging import debug_logger

# ------------------------------------------------------------------------------------
# Consts
HTTP_TIMEOUT = 30
MAX_PAGES = 1000
BATCH_SIZE = 1000  # reserved for future batch optimizations

# ------------------------------------------------------------------------------------
# Helpers

def _canon(o: Any) -> str:
    """Canonical JSON string for deterministic hashing."""
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def _hash_content_only(item: Dict[str, Any]) -> bytes:
    """Hash based purely on record content."""
    return hashlib.sha256(_canon(item).encode("utf-8")).digest()

def _as_list(payload: Any) -> List[Dict[str, Any]]:
    """
    Normalizes API responses into a list of dicts.
    Handles common shapes seen in third party APIs.
    """
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("data", "items", "results", "records", "rows"):
            v = payload.get(key)
            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]
        data = payload.get("data")
        if isinstance(data, dict):
            for key in ("items", "results", "records", "rows"):
                v = data.get(key)
                if isinstance(v, list):
                    return [x for x in v if isinstance(x, dict)]
        if all(isinstance(k, str) for k in payload.keys()):
            return [payload]
    return []

def _merge_page_param(base_url: str, page: int) -> str:
    """Attach or replace the page query param."""
    parts = urlsplit(base_url)
    qs = dict(parse_qsl(parts.query, keep_blank_values=True))
    qs["page"] = str(page)
    new_query = urlencode(qs, doseq=True)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))

def _maybe_next_url(payload: Any) -> str:
    """Discover a next page URL in cursor style APIs."""
    if not isinstance(payload, dict):
        return ""
    for key in ("next", "next_url", "nextPage", "next_page", "nextLink", "next_link"):
        v = payload.get(key)
        if isinstance(v, str) and v:
            return v
    links = payload.get("links") or payload.get("_links")
    if isinstance(links, dict):
        nxt = links.get("next")
        if isinstance(nxt, dict):
            href = nxt.get("href") or nxt.get("url")
            if isinstance(href, str) and href:
                return href
        if isinstance(nxt, str):
            return nxt
    return ""

def _progress(self, *, state: str = "PROGRESS", **meta):
    """Emit progress updates for the frontend."""
    try:
        self.update_state(state=state, meta=meta)
    except Exception:
        pass

# ------------------------------------------------------------------------------------
# Task

@celery.task(bind=True, name="app.tasks.extract_data_sources.extract_data_sources_task")
def extract_data_sources_task(self):
    """
    Walk all DataSource.base_url links with pagination, normalize items, hash content,
    and upsert into user_dataset_raw with global content hash dedupe.
    """
    task_id = self.request.id
    debug_logger.info(f"[EXTRACT] START task_id={task_id} extract data from connected sources")
    start_time = datetime.utcnow()
    out = {"processed": 0, "inserted": 0, "duplicates": 0, "errors": []}

    # Load sources
    try:
        sources = db.session.query(DataSource).all()
        debug_logger.info(f"[EXTRACT] Loaded {len(sources)} data sources from database")
    except Exception as e:
        debug_logger.error(f"[EXTRACT] FAILED to query data sources: {e}")
        return {"processed": 0, "inserted": 0, "duplicates": 0, "errors": [f"sources_query_failed: {e}"]}

    total_sources = len(sources)

    # Initial progress tick
    _progress(
        self,
        percent=0,
        processed=0,
        total=total_sources,
        inserted=0,
        duplicates=0,
        message="Starting ingestion",
        task_id=task_id,
    )

    for src in sources:
        out["processed"] += 1
        source_id = getattr(src, "id", None)
        source_name = getattr(src, "name", None)
        source_type = getattr(src, "source_type", None)
        user_id = getattr(src, "user_id", None)

        debug_logger.info(
            f"[EXTRACT] Processing source id={source_id} name='{source_name}' type={source_type} user_id={user_id}"
        )

        try:
            page = 1
            total_fetched_for_source = 0
            per_source_inserted = 0
            per_source_duplicates = 0
            now = datetime.utcnow()
            seen_hashes: set[bytes] = set()

            base_url = getattr(src, "base_url", None)
            if not base_url:
                msg = f"source_id={source_id} err=missing_base_url"
                debug_logger.warning(f"[EXTRACT] SKIP {msg}")
                out["errors"].append(msg)
                _progress(
                    self,
                    percent=int(out["processed"] * 100 / max(total_sources, 1)),
                    processed=out["processed"],
                    total=total_sources,
                    source_id=source_id,
                    source_name=source_name,
                    inserted=out["inserted"],
                    duplicates=out["duplicates"],
                    message="Skipped source missing base_url",
                    task_id=task_id,
                )
                continue

            next_url = ""

            while page <= MAX_PAGES:
                api_url = next_url if next_url else _merge_page_param(base_url, page)
                debug_logger.info(f"[EXTRACT] Fetching page {page} from {api_url} for source id={source_id}")
                debug_logger.debug(f"[EXTRACT] Using {'cursor next_url' if next_url else 'page parameter'} pagination")

                try:
                    r = requests.get(api_url, timeout=HTTP_TIMEOUT)
                    content_len = len(r.content) if r.content else 0
                    debug_logger.debug(f"[EXTRACT] HTTP {r.status_code} content_length={content_len} url={api_url}")
                    r.raise_for_status()

                    raw_json = r.json()
                    items = _as_list(raw_json)
                    debug_logger.debug(f"[EXTRACT] Parsed {len(items)} items from page {page} for source id={source_id}")

                except requests.exceptions.Timeout:
                    debug_logger.error(f"[EXTRACT] TIMEOUT fetching {api_url} after {HTTP_TIMEOUT}s")
                    raise
                except requests.exceptions.RequestException as req_e:
                    debug_logger.error(f"[EXTRACT] HTTP ERROR fetching {api_url}: {req_e}")
                    raise
                except (ValueError, json.JSONDecodeError) as json_e:
                    debug_logger.error(f"[EXTRACT] JSON DECODE ERROR from {api_url}: {json_e}")
                    raise

                if not items:
                    debug_logger.info(f"[EXTRACT] No items on page {page} for source id={source_id}")
                    _progress(
                        self,
                        percent=int(out["processed"] * 100 / max(total_sources, 1)),
                        processed=out["processed"],
                        total=total_sources,
                        source_id=source_id,
                        source_name=source_name,
                        page=page,
                        fetched_for_source=total_fetched_for_source,
                        inserted=out["inserted"],
                        duplicates=out["duplicates"],
                        message="No items; pagination complete",
                        task_id=task_id,
                    )
                    break

                # Build rows; avoid in run duplicates
                rows = []
                new_hashes = 0
                for idx, it in enumerate(items):
                    content_hash = _hash_content_only(it)
                    if content_hash in seen_hashes:
                        continue
                    seen_hashes.add(content_hash)
                    new_hashes += 1

                    rows.append({
                        "user_id": user_id,
                        "source_id": source_id,
                        "record_time": datetime.utcnow(),  # metadata only
                        "content": it,
                        "content_hash": content_hash,
                        "content_type": "json",
                        "status": "ok",
                        "error_message": None,
                    })

                    if idx < 3:
                        debug_logger.debug(f"[EXTRACT] Item {idx}: hash={content_hash.hex()[:16]}...")

                if new_hashes == 0:
                    debug_logger.warning(
                        f"[EXTRACT] Page {page} produced no new hashes for source id={source_id}. Stopping."
                    )
                    _progress(
                        self,
                        percent=int(out["processed"] * 100 / max(total_sources, 1)),
                        processed=out["processed"],
                        total=total_sources,
                        source_id=source_id,
                        source_name=source_name,
                        page=page,
                        fetched_for_source=total_fetched_for_source,
                        inserted=out["inserted"],
                        duplicates=out["duplicates"],
                        message="No new hashes; stopping pagination",
                        task_id=task_id,
                    )
                    break

                # Upsert each row; DB enforces unique(content_hash)
                debug_logger.info(
                    f"[EXTRACT] Upserting {len(rows)} records from page {page} source id={source_id}"
                )
                for row_idx, row_data in enumerate(rows):
                    try:
                        now_ts = datetime.utcnow()
                        row_data["ingested_at"] = now_ts
                        row_data["created_at"]  = now_ts

                        stmt  = mysql_insert(UserDatasetRaw).values(**row_data)
                        ondup = stmt.on_duplicate_key_update(
                            ingested_at   = row_data["ingested_at"],
                            status        = row_data["status"],
                            error_message = row_data["error_message"],
                        )
                        res = db.session.execute(ondup)
                        db.session.commit()

                        if res.rowcount == 1:
                            out["inserted"] += 1
                            per_source_inserted += 1
                        else:
                            out["duplicates"] += 1
                            per_source_duplicates += 1

                        if (row_idx + 1) % 200 == 0:
                            _progress(
                                self,
                                percent=int(out["processed"] * 100 / max(total_sources, 1)),
                                processed=out["processed"],
                                total=total_sources,
                                source_id=source_id,
                                source_name=source_name,
                                page=page,
                                fetched_for_source=total_fetched_for_source + (row_idx + 1),
                                inserted=out["inserted"],
                                duplicates=out["duplicates"],
                                message=f"Upserted {row_idx + 1}/{len(rows)} on page {page}",
                                task_id=task_id,
                            )

                    except Exception as e:
                        db.session.rollback()
                        debug_logger.warning(
                            f"[EXTRACT] Failed to upsert record {row_idx} from page {page}: {e}"
                        )
                        out["duplicates"] += 1
                        per_source_duplicates += 1

                total_fetched_for_source += len(rows)
                debug_logger.info(
                    f"[EXTRACT] Page {page} complete for source {source_id}: "
                    f"{len(rows)} processed, inserted={per_source_inserted}, duplicates={per_source_duplicates}, "
                    f"total_fetched_for_source={total_fetched_for_source}"
                )

                # Per page progress tick
                _progress(
                    self,
                    percent=int(out["processed"] * 100 / max(total_sources, 1)),
                    processed=out["processed"],
                    total=total_sources,
                    source_id=source_id,
                    source_name=source_name,
                    page=page,
                    fetched_for_source=total_fetched_for_source,
                    inserted=out["inserted"],
                    duplicates=out["duplicates"],
                    message=f"Processed page {page}",
                    task_id=task_id,
                )

                # Advance pagination
                next_url = _maybe_next_url(raw_json)
                page += 1

            # Update last_updated for this source
            try:
                src.last_updated = now
                db.session.commit()
                debug_logger.info(
                    f"[EXTRACT] Source id={source_id} completed: fetched={total_fetched_for_source} items across {page-1} pages"
                )
            except Exception as stamp_e:
                db.session.rollback()
                msg = f"source_id={source_id} err=last_updated_commit_failed: {stamp_e}"
                debug_logger.error(f"[EXTRACT] {msg}")
                out["errors"].append(msg)

            # Per source completion tick
            _progress(
                self,
                percent=int(out["processed"] * 100 / max(total_sources, 1)),
                processed=out["processed"],
                total=total_sources,
                source_id=source_id,
                source_name=source_name,
                inserted=out["inserted"],
                duplicates=out["duplicates"],
                message="Source complete",
                task_id=task_id,
            )

        except Exception as e:
            db.session.rollback()
            debug_logger.exception(
                f"[EXTRACT] FATAL ERROR processing source id={source_id} name='{source_name}': {e}"
            )
            out["errors"].append(f"source_id={source_id} err={e}")

            # Error progress tick
            _progress(
                self,
                percent=int(out["processed"] * 100 / max(total_sources, 1)),
                processed=out["processed"],
                total=total_sources,
                source_id=source_id,
                source_name=source_name,
                inserted=out["inserted"],
                duplicates=out["duplicates"],
                message=f"Error: {e}",
                task_id=task_id,
            )

    # Final summary
    end_time = datetime.utcnow()
    elapsed_seconds = (end_time - start_time).total_seconds()
    debug_logger.info(
        f"[EXTRACT] COMPLETE task_id={task_id} elapsed={elapsed_seconds:.2f}s "
        f"sources_processed={out['processed']} inserted={out['inserted']} "
        f"duplicates={out['duplicates']} errors={len(out['errors'])}"
    )

    if out["errors"]:
        debug_logger.warning(f"[EXTRACT] Errors encountered: {out['errors']}")

    # Final success state for the frontend
    _progress(
        self,
        state="SUCCESS",
        percent=100,
        processed=out["processed"],
        total=total_sources,
        inserted=out["inserted"],
        duplicates=out["duplicates"],
        message="Complete",
        task_id=task_id,
    )

    return out
