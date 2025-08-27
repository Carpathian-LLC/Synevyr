# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# Notes:
# - Settings routes and anythign that requires "auth" 
# ------------------------------------------------------------------------------------
# Imports:
from datetime import datetime
from io import BytesIO
import shlex
from flask import jsonify, request, session, Blueprint
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash
import pyotp
import secrets
import qrcode
import qrcode.image.svg

# Local Imports
from flask import current_app as app
from app.extensions import csrf, limiter, db

from app.utils.security import authorizeUser
from app.utils.helpers import validate_password
from app.utils.logging import log_activity, logger, unauthorized_logger
from app.utils.notifications import notify_user_login, send_email_verification

from app.models.user import User
from app.models.logging import ActivityLog

# ------------------------------------------------------------------------------------
# Var Decs
auth_bp = Blueprint('auth', __name__)

# ------------------------------------------------------------------------------------
# endpoints (routes)

# Master CSRF issuing logic - requires authenticated users
@auth_bp.route("/csrf-token", methods=["GET"])
def get_csrf_token():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "unauthorized"}), 403

    token = csrf.generate_csrf()
    response = jsonify({"csrf_token": token})
    response.set_cookie("X-CSRF-TOKEN", token,
        secure=True,
        samesite="Strict",
        httponly=False,
        max_age=3600,
        path="/"
    )
    return response

@auth_bp.route("/auth/delete-account", methods=["DELETE"])
@csrf.exempt
def delete_account():
    try:
        user_id = authorizeUser()

        # Step 1: delete all user's assets

        # ADD MORE EVENTUALLY


        # Step 4: delete user account
        user = db.session.get(User, user_id)

        if user and user.customer:
            db.session.expunge(user.customer)

        if user:
            db.session.delete(user)

        db.session.commit()
        session.clear()  
        logger.info("Deleted account and all associated resources for user_id=%s", user_id)
        return jsonify({"success": True}), 200

    except Exception as e:
        db.session.rollback()
        logger.error("Failed to delete account: %s", e, exc_info=True)
        return jsonify({"error": "Failed to delete account", "details": str(e)}), 500

@auth_bp.route("/auth/change-password", methods=["POST"])
@csrf.exempt
def change_password():
    logger.info("→ Incoming request to /auth/change-password")
    logger.info("Change-password request start")
    user_id = authorizeUser()
    logger.debug("Authenticated user_id=%s", user_id)

    data = request.get_json(silent=True) or {}
    current = data.get("currentPassword", "").strip()
    new = data.get("newPassword", "").strip()
    verify = data.get("verifyNewPassword", "").strip()

    # 1) Required fields
    if not current or not new or not verify:
        logger.warning("Missing field(s) in change-password for user_id=%s", user_id)
        return jsonify(message="Missing password field"), 400

    # 2) Match check
    if new != verify:
        logger.warning("Password mismatch for user_id=%s", user_id)
        return jsonify(message="Passwords do not match"), 400

    # 3) Strength check (reuse signup logic)
    is_valid, pwd_msg = validate_password(new)
    if not is_valid:
        logger.warning("Password strength validation failed for user_id=%s: %s", user_id, pwd_msg)
        return jsonify(message=pwd_msg), 400

    try:
        # 4) Verify current password
        user = db.session.get(User, user_id)

        if not user:
            logger.error("User not found for user_id=%s", user_id)
            return jsonify(message="User not found"), 404

        if not check_password_hash(user.password_hash, current):
            logger.warning("Incorrect current password for user_id=%s", user_id)
            return jsonify(message="Incorrect current password"), 400

        # 5) All good → update hash
        user.password_hash = generate_password_hash(new)
        db.session.commit()
        logger.info("Password updated successfully for user_id=%s", user_id)
        return jsonify(message="Password changed successfully"), 200

    except Exception as e:
        db.session.rollback()
        logger.exception("Unexpected error in change-password for user_id=%s", user_id)
        return jsonify(message="An unexpected error occurred. Please try again later."), 50

@auth_bp.route("/auth/2fa/status", methods=["GET"])
def get_2fa_status():
    user_id = authorizeUser()

    app.logger.info("Fetching 2FA status for user_id=%s", user_id)
    try:
        user = db.session.get(User, user_id)

        enabled = bool(user.two_fa_enabled)
        app.logger.debug("2FA status for user_id=%s: %s", user_id, enabled)
        return jsonify(enabled=enabled), 200
    except Exception as e:
        app.logger.exception("Error fetching 2FA status for user_id=%s", user_id)
        return jsonify(message="Failed to fetch 2FA status"), 500

@auth_bp.route("/auth/2fa/setup", methods=["GET"])
def setup_2fa():
    user_id = authorizeUser()

    app.logger.info("→ 2FA setup requested for user_id=%s", user_id)

    try:
        user = db.session.get(User, user_id)

        if not user:
            app.logger.error("User not found during 2FA setup user_id=%s", user_id)
            return jsonify(message="User not found"), 404

        if user.two_fa_enabled:
            app.logger.warning("2FA is already enabled for user_id=%s — denying setup request", user_id)
            return jsonify(message="2FA is already enabled"), 400

        # Only create new secret if not already present
        if not user.totp_secret:
            secret = pyotp.random_base32()
            user.totp_secret = secret
            db.session.commit()
            app.logger.debug("Stored new TOTP secret for user_id=%s", user_id)
        else:
            secret = user.totp_secret
            app.logger.debug("Reusing existing TOTP secret for user_id=%s", user_id)

        # Build provisioning URI
        issuer = "Carpathian Cloud"
        identity = getattr(user.customer, "email", None) or getattr(user.customer, "username", None) or f"user{user_id}"
        label = f"{issuer}:{identity}"
        uri = pyotp.TOTP(secret).provisioning_uri(name=label, issuer_name=issuer)

        # Generate QR code SVG
        factory = qrcode.image.svg.SvgImage
        img = qrcode.make(uri, image_factory=factory)
        buffer = BytesIO()
        img.save(buffer)
        svg = buffer.getvalue().decode("utf-8")
        app.logger.info("Generated QR code SVG for user_id=%s", user_id)

        return jsonify(qr=svg, secret=secret), 200

    except Exception as e:
        db.session.rollback()
        app.logger.exception("Error during 2FA setup for user_id=%s", user_id)
        return jsonify(message="Error setting up 2FA"), 500

@auth_bp.route("/auth/2fa/confirm", methods=["POST"])
@csrf.exempt
def confirm_2fa():
    user_id = authorizeUser()
    data = request.get_json(silent=True) or {}
    code = data.get("code", "").strip()
    app.logger.info("Confirming 2FA for user_id=%s with code=%s", user_id, code)

    if not code:
        return jsonify(message="Code is required"), 400

    try:
        user = db.session.get(User, user_id)

        if not user or not user.totp_secret:
            return jsonify(message="2FA setup not initialized"), 400

        if user.two_fa_enabled:
            app.logger.info("2FA is already confirmed for user_id=%s", user_id)
            return jsonify(message="2FA is already confirmed"), 400

        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(code, valid_window=1):
            app.logger.warning("Invalid 2FA code for user_id=%s", user_id)
            return jsonify(message="Invalid authentication code"), 400

        user.two_fa_enabled = True
        db.session.commit()
        app.logger.info("2FA confirmed and enabled for user_id=%s", user_id)
        log_activity(
            status_code=200,
            ip_address=request.remote_addr,
            user_id=user.id,
            event_message="Two-Factor Authentication enabled"
        )

        # Resend the cookie token
        session.clear()
        session["user_id"] = user.id
        return jsonify(message="2FA enabled", enabled=True), 200

    except Exception as e:
        db.session.rollback()
        app.logger.exception("Error confirming 2FA for user_id=%s", user_id)
        return jsonify(message="Could not confirm 2FA"), 500

@auth_bp.route("/auth/2fa/reset", methods=["POST"])
@csrf.exempt
def reset_2fa():
    user_id = authorizeUser()

    data = request.get_json() or {}
    password = data.get("password", "").strip()

    if not password:
        return jsonify(message="Password is required"), 400

    try:
        user = db.session.get(User, user_id)

        if not user:
            return jsonify(message="User not found"), 404

        if not user.check_password(password):
            return jsonify(message="Invalid password"), 403

        log_activity(
            status_code=200,
            ip_address=request.remote_addr,
            user_id=user.id,
            event_message="Two-Factor Authentication reset attempt"
        )
        # Revoke 2FA and create a new secret
        user.two_fa_enabled = False
        user.totp_secret = pyotp.random_base32()
        db.session.commit()

        # Generate QR from provisioning URI
        issuer = "Carpathian Cloud"
        identity = getattr(user.customer, "email", None) or getattr(user.customer, "username", None) or f"user{user_id}"
        label = f"{issuer}:{identity}"
        uri = pyotp.TOTP(user.totp_secret).provisioning_uri(name=label, issuer_name=issuer)

        factory = qrcode.image.svg.SvgImage
        img = qrcode.make(uri, image_factory=factory)
        buffer = BytesIO()
        img.save(buffer)
        svg = buffer.getvalue().decode("utf-8")

        return jsonify(qr=svg), 200

    except Exception as e:
        db.session.rollback()
        app.logger.exception("Error during 2FA reset for user_id=%s", user_id)
        return jsonify(message="Internal server error"), 500

@auth_bp.route("/auth/activity", methods=["GET"])
def get_activity():
    try:
        user_id = authorizeUser()
        logger.info("Fetching recent activity for user_id=%s", user_id)

        logs = (
            ActivityLog.query
            .filter_by(user_id=user_id)
            .order_by(ActivityLog.accessed_at.desc())
            .limit(10)
            .all()
        )

        logger.debug("Retrieved %d activity entries for user_id=%s", len(logs), user_id)

        result = [
            {
                "id": log.id,
                "event": log.event_message,
                "timestamp": log.accessed_at.isoformat(),
                "ip": log.ip_address,
                "status": log.status_code
            }
            for log in logs
        ]

        return jsonify(activity=result), 200

    except PermissionError:
        return jsonify(message="Unauthorized"), 403
    except Exception as e:
        app.logger.exception("Error fetching activity for user_id=%s", user_id)
        return jsonify(message="Failed to fetch activity"), 500

@auth_bp.route("/auth/whoami", methods=["GET"])
def get_user():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    logger.info("Fetched user: %s", user.username)
    logger.info("Customer info: %s", user.customer)

    if not user.customer:
        return jsonify({"error": "Customer data missing"}), 500

    return jsonify({
        "id": user.id,
        "username": user.username,
        "first_name": user.customer.first_name,
        "last_name": user.customer.last_name,
        "email": user.customer.email,
        "created_at": user.created_at.isoformat(),
        "status": user.status,
    })

# Verifies the user BEFORE login. THIS is the route that issues the token.
@auth_bp.route("/auth/2fa/verify", methods=["POST"])
@csrf.exempt
@limiter.limit("3 per minute")
def verify_2fa_login():
    """
    Verifies the 2FA code during login (before issuing JWT).
    Expects session['pre_2fa_user_id'] to be set.
    """
    user_id = session.get("pre_2fa_user_id")
    client_ip = request.remote_addr

    if not user_id:
        app.logger.warning("2FA verify failed: no session user from %s", client_ip)
        return jsonify(success=False, message="2FA session expired or invalid"), 401

    data = request.get_json(silent=True) or {}
    code = data.get("code", "").strip()
    app.logger.info("2FA verify attempt for user_id=%s from %s", user_id, client_ip)

    if not code:
        app.logger.debug("2FA verify failed: missing code for user_id=%s", user_id)
        return jsonify(success=False, message="2FA code is required"), 400

    try:
        user = db.session.get(User, user_id)

        if not user:
            app.logger.warning("2FA verify failed: user_id=%s not found", user_id)
            session.pop("pre_2fa_user_id", None)
            return jsonify(success=False, message="User not found"), 404

        if not user.totp_secret or not user.two_fa_enabled:
            app.logger.warning("2FA verify failed: user_id=%s missing TOTP or not enabled", user_id)
            session.pop("pre_2fa_user_id", None)
            return jsonify(success=False, message="2FA not properly configured"), 400

        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(code, valid_window=1):
            app.logger.warning("2FA verify failed: invalid code for user_id=%s", user_id)
            return jsonify(success=False, message="Invalid 2FA code"), 401

        notify_user_login(
            subject="🔐 Carpathian - New Login Detected",
            recipient=user.customer.email,
            customer=user.customer,
            ip_address=client_ip
        )

        try:
            session["user_id"] = user.id
            session.pop("pre_2fa_user_id", None)
            response = jsonify(success=True)
            log_activity(status_code=200,ip_address=client_ip, user_id=user.id, event_message="Successful login.")
            return response
        except Exception as e:
            app.logger.exception(f"[AUTH] Unexpected error while logging in user {user.username}")
            return jsonify(success=False, message="Internal server error"), 500

    except Exception as e:
        app.logger.exception("Unexpected error during 2FA verification for user_id=%s", user_id)
        return jsonify(success=False, message="Server error during 2FA verification"), 500

@auth_bp.route("/auth/email/verify-code", methods=["POST"])
@csrf.exempt
def verify_email_code():
    user_id = authorizeUser()
    try:
        data = request.get_json() or {}
        submitted_code = data.get("code", "").strip().upper()

        if not submitted_code:
            return jsonify({"success": False, "error": "Verification code is required."}), 400

        user = db.session.get(User, user_id)
        if not user:
            app.logger.warning("Verification attempt for nonexistent user_id=%s", user_id)
            return jsonify({"success": False, "error": "User not found."}), 404

        if user.status == "active":
            app.logger.info("User %s attempted to verify an already active account.", user.username)
            return jsonify({"success": False, "error": "Account is already verified."}), 400

        if not user.password_reset_token:
            app.logger.warning("User %s has no verification token stored.", user.username)
            return jsonify({"success": False, "error": "No verification code was issued."}), 400

        if user.password_reset_token.upper() != submitted_code:
            app.logger.warning("User %s provided incorrect verification code.", user.username)
            return jsonify({"success": False, "error": "Invalid verification code."}), 400

        if user.token_created_at and (datetime.now() - user.token_created_at).total_seconds() > 86400:
            app.logger.warning("Verification code for user %s has expired.", user.username)
            return jsonify({"success": False, "error": "Verification code has expired."}), 400

        # Mark user as verified
        user.status = "active"
        user.password_reset_token = None
        user.token_created_at = None

        db.session.commit()
        app.logger.info("User %s successfully verified their email.", user.username)
        return jsonify({"success": True}), 200

    except Exception as e:
        app.logger.exception("Unexpected error verifying email for user_id=%s", user_id)
        return jsonify({"success": False, "error": "Internal server error during verification."}), 500

@auth_bp.route("/auth/send-code", methods=["POST"])
@csrf.exempt
def send_verification_email():
    user_id = authorizeUser()
    try:
        user = db.session.get(User, user_id)
        if not user or user.status == "active":
            return jsonify({"error": "Invalid or already verified."}), 400
            # Notify the user about the successful account creation
        def generate_email_verification_code(length=8) -> str:
            return secrets.token_hex(length // 2).upper() 

        code = generate_email_verification_code()
        user.password_reset_token = code
        user.token_created_at = datetime.now()
        db.session.commit()
        
        send_email_verification(
            subject="🪪 Verify your Carpathian account",
            recipient=user.customer.email,
            customer=user.customer,
            token=code
        )
    except Exception as e:
        app.logger.exception("Unexpected error during sending email verification code for user_id=%s", user_id)
        return jsonify(success=False, message="Server error sending email code"), 500


    return jsonify({"success": True}), 200

@auth_bp.route("/auth/me", methods=["GET"])
def get_current_user_details():
    try:
        user_id = session.get("user_id")
        if not user_id:
            unauthorized_logger.warning("Unauthorized access attempt with no session.")
            return jsonify({"error": "Unauthorized access"}), 401
    except Exception as e:
        logger.error("Session error in get_current_user_details: %s", e, exc_info=True)
        return jsonify({"error": "Unauthorized"}), 401

    logger.debug(f"[AUTH] Session user_id resolved: {user_id}")

    try:
        user = db.session.get(User, user_id)
        if not user:
            logger.warning(f"[AUTH] No user found for ID: {user_id}, clearing session")
            session.clear()
            return jsonify(success=False, message="User not found"), 401

        user_details = {
            "id": user.id,
            "username": user.username,
            "status": user.status,
            "two_fa_enabled": user.two_fa_enabled,
        }

        logger.info(f"[AUTH] Retrieved profile for user {user.id}")
        return jsonify(success=True, user=user_details), 200

    except SQLAlchemyError as e:
        logger.error(f"[AUTH] DB error while fetching user {user_id}: {str(e)}")
        return jsonify(success=False, message="Database error"), 500

    except Exception as e:
        logger.exception(f"[AUTH] Unexpected error while resolving user {user_id}")
        return jsonify(success=False, message="Internal server error"), 500
