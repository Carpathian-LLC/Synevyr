# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Authorized.
# ------------------------------------------------------------------------------------
# Notes:
# - Open data sources (no auth, no CSRF)
# ------------------------------------------------------------------------------------
# Imports:
from datetime import date, datetime
import time
import uuid
from flask_mail import Message
from flask import jsonify, render_template, request, session, Blueprint
from sqlalchemy import desc
from werkzeug.security import generate_password_hash
import secrets
from sqlalchemy.sql import text

# Local Imports
from flask import current_app as app
from app.extensions import csrf, limiter, db
from app.utils.logging import logger

# ------------------------------------------------------------------------------------
# Vars
public_bp = Blueprint('public', __name__)

# ------------------------------------------------------------------------------------
# Helpers

def _host_base() -> str:
    # Ensure no trailing slash
    return request.host_url.rstrip('/')

def _usage_payload(endpoint: str, *, table: str | None, allowed_tables: set[str] | None) -> dict:
    """
    Build a standard usage payload for empty datasets.
    endpoint: literal path like "/public/user_customers" or "/public/analytics"
    table: the specific table being queried, or None if not applicable
    allowed_tables: when relevant, list of accepted table names for the endpoint
    """
    params = {
        "page": "Page number. Default 1.",
        "page_size": "Rows per page. Default 50. Max 500."
    }

    examples = []

    if endpoint == "/public/analytics":
        params = {
            **params,
            "table": f"Target table. Allowed: {sorted(list(allowed_tables)) if allowed_tables else ['customer_analysis','cx_stats']}"
        }
        # Provide one example per allowed table for clarity
        for t in (sorted(list(allowed_tables)) if allowed_tables else ["customer_analysis", "cx_stats"]):
            examples.append(f"{_host_base()}{endpoint}?table={t}&page=1&page_size=50")
    else:
        # Specific single-table endpoints
        base_example = f"{_host_base()}{endpoint}?page=1&page_size=50"
        examples.append(base_example)

    message = f"No data available in table '{table}'." if table else "No data available."

    return {
        "message": message,
        "usage": {
            "endpoint": endpoint,
            "method": "GET",
            "parameters": params,
            "examples": examples
        }
    }

def _get_pagination_args() -> tuple[int, int, int]:
    page = max(int(request.args.get("page", 1)), 1)
    page_size = min(int(request.args.get("page_size", 50)), 500)
    offset = (page - 1) * page_size
    return page, page_size, offset

# ------------------------------------------------------------------------------------
# Generic public table fetcher

def fetch_public_table_data(table: str, allowed_tables: set[str], endpoint_path: str | None = None):
    if table not in allowed_tables:
        return jsonify({"error": "Invalid table"}), 400

    page, page_size, offset = _get_pagination_args()

    # Counts
    count_query = text(f"SELECT COUNT(*) FROM {table}")
    total_items = db.session.execute(count_query).scalar()
    total_pages = (total_items + page_size - 1) // page_size if total_items else 0

    # When empty, return usage block
    if total_items == 0:
        return jsonify(_usage_payload(endpoint_path or request.path, table=table, allowed_tables=allowed_tables)), 200

    # Data slice
    data_query = text(f"SELECT * FROM {table} LIMIT :limit OFFSET :offset")
    results = db.session.execute(data_query, {"limit": page_size, "offset": offset}).mappings().all()

    return jsonify({
        "table": table,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "total_items": total_items,
        "data": [dict(row) for row in results]
    })

# ------------------------------------------------------------------------------------
# Public Endpoints

@public_bp.route("/public/user_customers", methods=["GET"])
def public_user_customers():
    return fetch_public_table_data("user_customers", {"user_customers"}, endpoint_path="/public/user_customers")

@public_bp.route("/public/meta_leads", methods=["GET"])
def public_meta_leads():
    return fetch_public_table_data("meta_leads", {"meta_leads"}, endpoint_path="/public/meta_leads")

@public_bp.route("/public/wc_orders", methods=["GET"])
def public_wc_orders():
    return fetch_public_table_data("wc_orders", {"wc_orders"}, endpoint_path="/public/wc_orders")
