# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# Notes:
# - Primary Background Celery Init/Config (single app for worker + beat)
# ------------------------------------------------------------------------------------
# Imports
from flask import Flask
from celery.signals import after_setup_logger, after_setup_task_logger
from app.extensions import celery
from app.utils.logging import celery_logger
# ------------------------------------------------------------------------------------
# Vars
UPDATE_INTERVAL = 21600  # 6 hours 
CLEAN_INTERVAL = 21600   # 6 hours

# ------------------------------------------------------------------------------------
# Functions
def _redact_url(u: str) -> str:
    # e.g. redis://user:****@host:port/db
    try:
        from urllib.parse import urlsplit, urlunsplit
        s = urlsplit(u)
        netloc = s.netloc
        if "@" in netloc and ":" in netloc.split("@", 1)[0]:
            user = netloc.split("@", 1)[0].split(":", 1)[0]
            host = netloc.split("@", 1)[1]
            netloc = f"{user}:****@{host}"
        return urlunsplit((s.scheme, netloc, s.path, s.query, s.fragment))
    except Exception:
        return u

def init_celery(flask_app: Flask):
    # 1) Pull broker/backend from Flask config and validate
    try:
        broker = flask_app.config["CELERY_BROKER_URL"]
        backend = flask_app.config["CELERY_RESULT_BACKEND"]
    except KeyError as e:
        raise RuntimeError(f"Missing Celery config key in Flask app.config: {e}") from e

    # 2) Apply config to Celery (lowercase conf keys)
    celery.conf.update(
        broker_url=broker,
        result_backend=backend,
        task_track_started=True,
        task_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        beat_max_loop_interval=min(UPDATE_INTERVAL, 60),
    )
    celery_logger.info(
        f"[CELERY] env={flask_app.config.get('ENV')} "
        f"broker={_redact_url(broker)} backend={_redact_url(backend)}"
    )

    # 3) Force Celery to use our logger handlers for both app and task loggers
    @after_setup_logger.connect
    def _hook_root_logger(logger, *args, **kwargs):
        logger.handlers = celery_logger.handlers
        logger.setLevel(celery_logger.level)

    @after_setup_task_logger.connect
    def _hook_task_logger(logger, *args, **kwargs):
        logger.handlers = celery_logger.handlers
        logger.setLevel(celery_logger.level)

    # 4) Ensure Flask app context for every task (capture the bound callable)
    app_context = flask_app.app_context
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        def __call__(self, *args, **kwargs):
            with app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask

    # 5) Register all task modules BEFORE beat starts dispatching
    import app.tasks.extract_data_sources   # noqa: F401
    import app.tasks.transform_data          # noqa: F401 
    import app.tasks.load_analytics          # noqa: F401

    # 6) Define Beat schedule AFTER conf.update so it isn't clobbered elsewhere
    celery.conf.beat_schedule = {
        "extract-data-sources": {
            "task": "app.tasks.extract_data_sources.extract_data_sources_task",
            "schedule": UPDATE_INTERVAL,
            # "options": {"queue": "ingest"},  # uncomment if you route to a dedicated queue
        },
        "transform-clean-data": { 
            "task": "app.tasks.transform_data.transform_data_task",
            "schedule": CLEAN_INTERVAL,
            # "options": {"queue": "etl"},
        },
    }

    return celery
