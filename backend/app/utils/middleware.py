# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# Notes:
# - Middleware clients for logging user requests
# ------------------------------------------------------------------------------------
# Imports:

from datetime import datetime
from werkzeug.exceptions import HTTPException
from flask import render_template, request, session, g, Blueprint
from flask_limiter import RateLimitExceeded
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, decode_token
from flask_jwt_extended.exceptions import NoAuthorizationError
from flask_wtf.csrf import CSRFError


# Local Imports
from app.extensions import db

from app.models.plan import Plan
from app.models.user import GuestUser
from app.models.logging import SiteSecurityLog

from app.utils.logging import http_logger, unauthorized_logger, generate_guest_id

# ------------------------------------------------------------------------------------
# Vars
middleware_bp = Blueprint('middleware', __name__)

# ------------------------------------------------------------------------------------
# Functions

@middleware_bp.before_request
def global_request_filter_and_session_and_cname():
    # 1) Protocol check
    protocol = request.environ.get("SERVER_PROTOCOL", "")
    http_logger.debug("Protocol received: %s", protocol)
    if protocol not in ("HTTP/1.1", "HTTP/2.0"):
        http_logger.warning("Unsupported protocol: %s", protocol)
        sec = SiteSecurityLog(
            ip_address    = request.remote_addr,
            user_id       = session.get("user_id"),
            guest_id      = session.get("guest_id"),
            event_type    = "unsupported_protocol",
            event_message = f"Rejected protocol {protocol}",
            path          = request.path,
            method        = request.method,
            status_code   = 400,
            user_agent    = request.headers.get("User-Agent"),
        )
        db.session.add(sec)
        db.session.commit()
        return "Unsupported protocol", 400

    # 2) Resolve guest_id
    cookie_id = request.cookies.get("guest_id")
    session_id = session.get("guest_id")
    http_logger.debug("Cookie guest_id: %s, Session guest_id: %s", cookie_id, session_id)

    guest_id = cookie_id or session_id
    new_guest = False
    if not guest_id:
        guest_id = generate_guest_id()
        new_guest = True
        http_logger.info("Generated new guest_id: %s", guest_id)
    else:
        source = "cookie" if cookie_id else "session"
        http_logger.info("Using existing guest_id from %s: %s", source, guest_id)

    session["guest_id"] = guest_id

    # 3) Fetch or create GuestUser
    ip_address = request.remote_addr or "0.0.0.0"
    http_logger.debug("Client IP address: %s", ip_address)
    guest = GuestUser.query.filter_by(guest_id=guest_id).first()

    if not guest and new_guest:
        http_logger.info("No GuestUser found; creating new record for %s", guest_id)
        default_plan = Plan.query.filter_by(name="unregistered").first()
        if not default_plan:
            http_logger.error("Default 'unregistered' plan not found")
            raise RuntimeError("Default 'unregistered' plan not found.")
        guest = GuestUser(
            guest_id       = guest_id,
            ip_address     = ip_address,
            plan_id        = default_plan.id,
            status         = "active",
            created_at     = datetime.now(),
            first_seen     = datetime.now(),
            last_seen      = datetime.now(),
            visit_count    = 1,
            session_count  = 1,
            user_agent     = request.headers.get("User-Agent"),
            referrer       = request.referrer,
        )
        db.session.add(guest)
        db.session.commit()
        session["guest_seen"] = True
        g.guest_user = guest
        http_logger.info("GuestUser created (id=%s)", guest.id)

    elif guest:
        g.guest_user = guest
        http_logger.info("Found existing GuestUser (id=%s, visits=%s, sessions=%s)",
                    guest.id, guest.visit_count, guest.session_count)
        if not session.get("guest_seen"):
            guest.visit_count += 1
            if guest.ip_address != ip_address:
                guest.ip_address = ip_address
                guest.session_count += 1
                http_logger.info("IP changed; session_count incremented to %s", guest.session_count)
            guest.last_seen  = datetime.now()
            guest.user_agent = request.headers.get("User-Agent")
            guest.referrer   = request.referrer
            db.session.commit()
            session["guest_seen"] = True
            http_logger.info("Updated GuestUser (visit_count=%s, last_seen=%s)",
                        guest.visit_count, guest.last_seen)
        else:
            http_logger.debug("Session already marked seen; no update performed")

    else:
        http_logger.error("Unexpected state: guest_id=%s but no new_guest flag and no record found", guest_id)

    # 4) CNAME handling
    domain = request.host.lower()
    http_logger.debug("Host header: %s", domain)
    if domain != "api.carpathian.ai" and "." in domain and len(domain) <= 253:
        http_logger.info("Serving CNAME page for domain: %s", domain)
        return render_template("cname.html", domain=domain), 200

@middleware_bp.after_request
def set_guest_cookie(response):
    guest_id = session.get("guest_id")
    if guest_id:
        response.set_cookie(
            "guest_id", guest_id,
            max_age=60*60*24*365*2,
            httponly=True,
            secure=True,
            samesite="Lax",
        )
        http_logger.debug("Set guest_id cookie: %s", guest_id)
    else:
        http_logger.debug("No guest_id in session; cookie not set")
    return response

@middleware_bp.errorhandler(404)
def handle_404(e):
    http_logger.warning(f"404 Not Found: {request.path}")
    return render_template(
        "error.html",
        error_code=404,
        title="Uh Oh... Looks like that page doesn't exist.",
        message="Check the docs or try another link."
    ), 404

@middleware_bp.errorhandler(RateLimitExceeded)
def handle_rate_limit_error(e):
    http_logger.warning(f"Rate limit exceeded for IP {request.remote_addr}: {e.description}")
    return render_template(
        "error.html",
        error_code=429,
        title="Too Many Requests",
        message="You’ve sent too many requests. Please wait a bit and try again."
    ), 429

@middleware_bp.errorhandler(NoAuthorizationError)
def handle_missing_auth(e):
    unauthorized_logger.warning(f"Unauthorized access on {request.path}")
    return render_template(
        "error.html",
        error_code=401,
        title="Unauthorized",
        message="I need to see some ID first before I let you in."
    ), 401

@middleware_bp.errorhandler(CSRFError)
def handle_csrf_error(e):
    unauthorized_logger.error(f"CSRF error: {e.description}")
    return render_template(
        "error.html",
        error_code=400,
        title="ERROR CODE: 400-01CSRF",
        message="Uh oh... I'm missing one line of code. Please try again."
    ), 400

@middleware_bp.errorhandler(405)
def handle_method_not_allowed(e):
    http_logger.warning(f"405 Method Not Allowed: {request.method} on {request.path}")
    return render_template(
        "error.html",
        error_code=405,
        title="Method Not Allowed",
        message=f"You used {request.method}, but that's not allowed here."
    ), 405

@middleware_bp.errorhandler(Exception)
def handle_generic_error(error):
    code = 500
    title = "500 Reasons to Say Sorry"
    message = "Something broke on our end, but we're fixing it."

    if isinstance(error, HTTPException):
        code = error.code
        if code == 429:
            title = "Woah there!"
            message = "That's more requests than I can handle right now."
        elif code == 403:
            title = "Access Denied"
            message = "You're not allowed to see that."
        elif code == 400:
            title = "Bad Request"
            message = "There was something wrong with your request."
        else:
            title = f"Error {code}"
            message = error.description or message

    http_logger.error(f"Error {code}: {error}", exc_info=True)
    return render_template(
        "error.html",
        error_code=code,
        title=title,
        message=message
    ), code
