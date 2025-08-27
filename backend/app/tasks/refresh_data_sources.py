# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# Notes:
# Minimal dataset ingestion task
# Scheduling:
#   - This task is scheduled by Celery Beat to run automatically every 6 hours.
#   - You can also kick it off early via the POST /tasks/run/update-data-sources route.
# Progress:
#   - Frontend can poll /tasks/<task_id>/status to read self.update_state(meta=...) progress.
# ------------------------------------------------------------------------------------

# Imports:
from datetime import datetime
import hashlib
import json
import requests
from sqlalchemy.exc import IntegrityError

from app.extensions import celery, db
from app.models.data_sources import DataSource, UserDatasetRaw

# ------------------------------------------------------------------------------------
# Consts
HTTP_TIMEOUT = 30
MAX_PAGES = 1000  # safeguard to avoid infinite loops

# ------------------------------------------------------------------------------------
# Helpers

def _canon(o):
    """Canonical JSON string for deterministic hashing."""
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def _hash32(item):
    """
    Generates a stable digest for a given item, using its ID if available.
    Falls back to canonical JSON if no ID present.
    Returns raw 32-byte SHA-256 digest (works with BINARY(32) columns).
    """
    key = None
    if isinstance(item, dict):
        key = item.get("id") or item.get("uuid") or item.get("external_id")
    s = str(key) if key is not None else _canon(item)
    return hashlib.sha256(s.encode("utf-8")).digest()

def _as_list(payload):
    """Normalizes API responses into a list of dicts."""
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        return [x for x in payload["data"] if isinstance(x, dict)]
    return [payload] if isinstance(payload, dict) else []

# ------------------------------------------------------------------------------------
# Task

@celery.task(bind=True, name="app.tasks.refresh_data_sources.update_data_sources_task")
def update_data_sources_task(self):
    """
    Ingests raw dataset items from all registered DataSource rows.

    Preserved behavior:
    - Query all DataSource rows
    - Paginate vendor API (?page=N) with hard cap MAX_PAGES
    - Bulk insert into user_dataset_raw; on unique constraint, fallback row-by-row, counting duplicates
    - Update each DataSource.last_updated to 'now' after success
    - Return aggregate counters

    Scheduling & manual kickoff:
    - Runs automatically every 6 hours via Celery Beat (configured elsewhere)
    - Can be manually triggered via POST /tasks/run/update-data-sources

    Progress reporting:
    - Uses self.update_state(state="PROGRESS", meta={...}) so the frontend can poll
      /tasks/<task_id>/status and render a progress bar without Socket.IO
    """
    out = {"processed": 0, "inserted": 0, "duplicates": 0, "errors": []}

    # Load source list
    try:
        sources = db.session.query(DataSource).all()
    except Exception as e:
        return {
            "processed": 0,
            "inserted": 0,
            "duplicates": 0,
            "errors": [f"sources_query_failed: {e}"],
        }

    total_sources = len(sources)

    # Initial progress tick
    try:
        self.update_state(
            state="PROGRESS",
            meta={
                "percent": 0,
                "processed": 0,
                "total": total_sources,
                "inserted": 0,
                "duplicates": 0,
                "message": "Starting ingestion",
            },
        )
    except Exception:
        pass

    for src in sources:
        out["processed"] += 1
        try:
            page = 1
            total_fetched_for_source = 0
            now = datetime.utcnow()

            base_url = getattr(src, "base_url", None)
            if not base_url:
                out["errors"].append(f"source_id={getattr(src, 'id', None)} err=missing_base_url")
                # progress tick for skipped source
                try:
                    percent = int(out["processed"] * 100 / max(total_sources, 1))
                    self.update_state(
                        state="PROGRESS",
                        meta={
                            "percent": percent,
                            "processed": out["processed"],
                            "total": total_sources,
                            "source_id": getattr(src, "id", None),
                            "source_name": getattr(src, "name", None),
                            "inserted": out["inserted"],
                            "duplicates": out["duplicates"],
                            "message": "Skipped source (missing base_url)",
                        },
                    )
                except Exception:
                    pass
                continue

            while page <= MAX_PAGES:
                r = requests.get(f"{base_url}?page={page}", timeout=HTTP_TIMEOUT)
                r.raise_for_status()
                items = _as_list(r.json())

                if not items:
                    break  # no more pages

                rows = []
                for it in items:
                    rows.append(
                        {
                            "user_id": getattr(src, "user_id", None),
                            "source_id": getattr(src, "id", None),
                            "record_time": now,
                            "content": it,
                            "content_hash": _hash32(it),
                            "content_type": "json",
                            "status": "ok",
                        }
                    )

                total_fetched_for_source += len(rows)

                # Bulk insert for performance
                try:
                    db.session.bulk_insert_mappings(UserDatasetRaw, rows)
                    db.session.commit()
                    out["inserted"] += len(rows)
                except IntegrityError:
                    # Fallback row-by-row to separate true duplicates
                    db.session.rollback()
                    for row in rows:
                        try:
                            db.session.execute(UserDatasetRaw.__table__.insert().values(**row))
                            db.session.commit()
                            out["inserted"] += 1
                        except IntegrityError:
                            db.session.rollback()
                            out["duplicates"] += 1

                # Emit page-level progress
                try:
                    percent = int(out["processed"] * 100 / max(total_sources, 1))
                    self.update_state(
                        state="PROGRESS",
                        meta={
                            "percent": percent,
                            "processed": out["processed"],
                            "total": total_sources,
                            "source_id": getattr(src, "id", None),
                            "source_name": getattr(src, "name", None),
                            "page": page,
                            "fetched_for_source": total_fetched_for_source,
                            "inserted": out["inserted"],
                            "duplicates": out["duplicates"],
                            "message": f"Processed page {page}",
                        },
                    )
                except Exception:
                    pass

                page += 1

            # Stamp last_updated for this source
            try:
                src.last_updated = now
                db.session.commit()
            except Exception:
                db.session.rollback()
                out["errors"].append(
                    f"source_id={getattr(src, 'id', None)} err=last_updated_commit_failed"
                )

        except Exception as e:
            db.session.rollback()
            out["errors"].append(f"source_id={getattr(src, 'id', None)} err={e}")

        # Per-source completion tick
        try:
            percent = int(out["processed"] * 100 / max(total_sources, 1))
            self.update_state(
                state="PROGRESS",
                meta={
                    "percent": percent,
                    "processed": out["processed"],
                    "total": total_sources,
                    "source_id": getattr(src, "id", None),
                    "source_name": getattr(src, "name", None),
                    "inserted": out["inserted"],
                    "duplicates": out["duplicates"],
                    "message": "Source complete",
                },
            )
        except Exception:
            pass

    return out
