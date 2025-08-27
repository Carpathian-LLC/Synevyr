# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# Notes:
# - routes for all the general home pages
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

# Local Imports
from app.core.config import BACKEND_VERSION, FRONTEND_VERSION
from flask import current_app as app
from app.extensions import csrf, limiter, db, mail
from flask import current_app

from app.models.general import BadgeDefinition, EarnedBadge
from app.models.general import Notification, NotificationLocation
from app.models.logging import FailedLoginAttempt, HoneypotLog
from app.models.user import Customer, Referral, User
from app.models.plan import Plan

from app.utils.security import authorizeUser
from app.utils.helpers import generate_referral_code, hash_input, validate_email_format, validate_password, validate_username
from app.utils.logging import log_activity, logger, bad_url_logger
from app.utils.notifications import award_badge_by_name, notify_user_login, send_email_verification, send_referral_invitation_email

# ------------------------------------------------------------------------------------
# Vars
general_bp = Blueprint('general', __name__)

# ------------------------------------------------------------------------------------
# endpoints (routes)

@general_bp.route('/')
@limiter.limit("10 per minute") 
def index():
    return render_template('index.html')

@general_bp.route('/dashboard')
def dashboard():
    return render_template("dashboard.html")

@general_bp.route("/version")
def get_version():
    return FRONTEND_VERSION, 200, {"Content-Type": "text/plain"}

@general_bp.route('/contact', methods=['POST'])
@csrf.exempt
@limiter.limit("3 per minute")
def contact_us():
    data = request.get_json()
    name = data.get("name", "Anonymous")
    email = data.get("email", "No email provided")
    subject = data.get("subject", "💬 New Contact Message")
    message_text = data.get("message", "No message provided")
    client_ip = request.remote_addr

    # Build the HTML email body
    html_body = f"""
    <html>
        <body>
            <p>You have received a new contact message from your website.</p>
            <p><strong>Name:</strong> {name}</p>
            <p><strong>Email:</strong> <a href="mailto:{email}">{email}</a></p>
            <p><strong>Subject:</strong> {subject}</p>
            <p><strong>Message:</strong><br>{message_text}</p>
            <hr>
            <p><strong>IP Address:</strong> {client_ip}</p>
            <p><strong>Date/Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </body>
    </html>
    """

    try:
        msg = Message(
            subject=subject,
            recipients=["malkasian@carpathian.ai"],  # Default recipient
            html=html_body
        )
        mail.send(msg)
        return jsonify({"message": "Your message has been sent successfully."}), 200
    except Exception as e:
        logger.error(f"Failed to send contact email: {e}")
        return jsonify({"message": "There was an error sending your message."}), 500

@general_bp.route("/feedback", methods=["POST"])
@csrf.exempt
@limiter.limit("2 per minute")
def user_feedback():
    try:
        data = request.get_json() or {}
    except Exception as e:
        logger.error(f"Failed to parse JSON from request: {e}")
        return jsonify({"message": "Invalid request format."}), 400

    message = data.get("message", "").strip()
    if not message:
        logger.warning("Feedback submitted without a message.")
        message = "No message provided"

    location = data.get("location", "Unknown location")

    client_ip = request.remote_addr or "Unknown IP"
    if client_ip == "Unknown IP":
        logger.warning("Could not determine client IP address.")

    try:
        user_id = authorizeUser()
    except Exception as e:
        logger.error(f"Failed to extract JWT identity: {e}")
        return jsonify({"message": "Authentication error."}), 401

    try:
        user = db.session.get(User, user_id)
    except Exception as e:
        logger.error(f"Database error retrieving user {user_id}: {e}")
        user = None

    try:
        user_email = user.customer.email if user and user.customer else "Unknown"
        username = user.username if user else "Unknown User"
    except Exception as e:
        logger.warning(f"Error accessing user details for user_id {user_id}: {e}")
        user_email = "Unknown"
        username = "Unknown User"

    html_body = f"""
    <html>
        <body>
            <p>You have received new user feedback from {username}.</p>
            <p>User Email: {user_email}</p>
            <p><strong>Location ID:</strong> {location}</p>
            <p><strong>Message:</strong><br>{message}</p>
            <hr>
            <p><strong>IP Address:</strong> {client_ip}</p>
            <p><strong>Date/Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </body>
    </html>
    """

    try:
        msg = Message(
            subject=f"💬 New Feedback from {location}",
            recipients=["malkasian@carpathian.ai"],
            html=html_body
        )
        mail.send(msg)
        logger.info(f"Feedback email sent successfully from user_id={user_id}, IP={client_ip}")
        return jsonify({"message": "Feedback received. Thank you!"}), 200
    except Exception as e:
        logger.error(f"Failed to send feedback email: {e}")
        return jsonify({"message": "There was an error processing your feedback."}), 500

@general_bp.route('/login', methods=['POST'])
@csrf.exempt
@limiter.limit("3 per minute")
def login():
    MAX_ATTEMPTS = current_app.config["MAX_ATTEMPTS"]
    SUSPENSION_TIME = current_app.config["SUSPENSION_TIME"]
    IP_BLOCK_TIME = current_app.config["IP_BLOCK_TIME"]
    MAX_IP_ATTEMPTS = current_app.config["MAX_IP_ATTEMPTS"]
    client_ip = request.remote_addr
    logger.info("Login attempt from %s", client_ip)

    # Parse JSON
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        logger.warning("Malformed JSON from %s", client_ip, exc_info=True)
        return jsonify(success=False, errors={"general": "Invalid JSON"}), 400

    # Validate inputs
    username = (data.get('username') or '').strip().lower()
    password = (data.get('password') or '').strip()
    errors = {}
    if not username or not validate_username(username):
        errors['username'] = "Invalid username format."
    if not password:
        errors['password'] = "Password cannot be empty."
    if errors:
        logger.debug("Validation errors %s from %s", errors, client_ip)
        return jsonify(success=False, errors=errors), 400

    # IP throttling
    cutoff = datetime.now() - IP_BLOCK_TIME
    recent = (
        FailedLoginAttempt.query
        .filter_by(ip_address=client_ip)
        .filter(FailedLoginAttempt.timestamp > cutoff)
        .count()
    )
    if recent >= MAX_IP_ATTEMPTS:
        logger.warning("IP %s blocked", client_ip)
        log_activity(status_code=429, ip_address=client_ip, event_message="Too many login attempts. Login temporarily blocked.")
        return jsonify(
            success=False,
            errors={"general": "Too many attempts—try again later."}
        ), 429

    # Lookup user
    user = User.query.filter_by(username=username).first()
    if not user:
        # record failed attempt
        db.session.add(FailedLoginAttempt(ip_address=client_ip, timestamp=datetime.now()))
        db.session.commit()
        logger.info("Unknown user %s from %s", username, client_ip)
        return jsonify(success=False, errors={"username": "User does not exist."}), 404

    # Check suspension
    if user.is_suspended and user.suspension_end and datetime.now() < user.suspension_end:
        logger.warning("Suspended user %s", user.id)
        return jsonify(
            success=False,
            errors={"general": "Your account is suspended."}
        ), 403

    # Verify password
    if not user.check_password(password):
        user.failed_attempts += 1
        user.last_failed_login = datetime.now()
        if user.failed_attempts >= MAX_ATTEMPTS:
            user.is_suspended = True
            user.suspension_end = datetime.now() + SUSPENSION_TIME
            log_activity(status_code=403, ip_address=client_ip, user_id=user.id, event_message="Login blocked: Account suspended.")
            err = "Temporarily suspended due to failed logins."
            logger.warning("User %s suspended until %s", user.id, user.suspension_end)
        else:
            err = "Invalid password."
            log_activity(status_code=401, ip_address=client_ip, user_id=user.id, event_message="Failed login attempt: Wrong password.")
            logger.info("Wrong password for user %s", user.id)
        db.session.commit()
        return jsonify(success=False, errors={"general": err}), 401

    # Reset counters on successful password
    user.failed_attempts = 0
    user.last_successful_login = datetime.now()
    user.last_login_ip = client_ip
    db.session.commit()
    
    # 2FA path
    if user.two_fa_enabled:
        session.clear()
        session["pre_2fa_user_id"] = user.id
        logger.info("2FA required for user %s", user.id)
        return jsonify(success=True, two_fa_required=True), 200
    try:
        notify_user_login(
            subject="🔐 Carpathian - New Login Detected",
            recipient=user.customer.email,
            customer=user.customer,
            ip_address=client_ip
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify(success=False, message="Internal server error"), 500

    try:
        session.clear()
        session["user_id"] = user.id
        response = jsonify(success=True)
        log_activity(status_code=200, ip_address=client_ip, user_id=user.id, event_message="Successful login.")
        return response
    except Exception as e:
        app.logger.exception(f"[AUTH] Unexpected error while logging in user {user.username}")
        return jsonify(success=False, message="Internal server error"), 500

@general_bp.route('/logout', methods=['POST'])
@csrf.exempt
def logout():
    session.clear()
    response = jsonify({"success": True, "message": "Logged out successfully"})
    response.set_cookie('session', '', expires=0)  # Expire the session cookie manually
    return response, 200

@general_bp.route('/signup', methods=['POST'])
@limiter.limit("3 per minute")
@csrf.exempt
def signup():
    """
    Signup endpoint that accepts JSON input.
    Example input:
    {
      "first_name": "John",
      "last_name": "Doe",
      "email": "john@example.com",
      "username": "johndoe",
      "password": "secret123",
      "password_confirm": "secret123"
    }
    """
    data = request.get_json() or {}
    ref_code = data.get("referral_code", "").strip()
    username = data.get('username', '').strip().lower()
    password = data.get('password', '').strip()
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    email = data.get('email', '').strip().lower()
    password_confirm = data.get('password_confirm', '').strip()

    logger.debug("Signup attempt: username=%s, email=%s", username, email)
    errors = {}
    form_data = {"first_name": first_name, "last_name": last_name, "email": email, "username": username}

    # Validate inputs
    # ref_owner = db.session.query(User).filter_by(referral_code=ref_code).first()
    # if not ref_owner:
    #     errors['auth_code'] = "Invalid referral code. Please sign up using the referral link in your email."
    if not validate_email_format(email):
        errors['email'] = "Invalid email format."
    if not validate_username(username):
        errors['username'] = "Invalid username. It must be 3-30 characters and only include letters, numbers, and underscores."
    
    is_valid_password, password_message = validate_password(password)
    if password and not is_valid_password:
        errors['password'] = password_message
    if password != password_confirm:
        errors['password_confirm'] = "Passwords do not match."

    # Check for existing username
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        errors['username'] = "Username already exists."
        logger.debug("Existing user found for username: %s", username)
    else:
        logger.debug("No user found for username: %s", username)

    # Check for existing email
    existing_customer = Customer.query.filter_by(email=email).first()
    if existing_customer:
        errors['email'] = "Email already registered."
        logger.debug("Existing customer found for email: %s", email)
    else:
        logger.debug("No customer found for email: %s", email)

    if errors:
        logger.info("Signup validation failed for %s with errors: %s", username, errors)
        return jsonify(success=False, errors=errors, form_data=form_data), 400

    try:
        default_plan = Plan.query.filter_by(name="registered").first()
        if not default_plan:
            raise Exception("Default plan not found.")

        username_hash = hash_input(username)
        referral_code = generate_referral_code()
        referred_by = None

        if ref_code:
            referrer = User.query.filter_by(referral_code=ref_code).first()
            if referrer:
                referred_by = referrer.id

        # Create user
        new_user = User(
            username=username,
            password_hash=generate_password_hash(password),
            plan_id=default_plan.id,
            status="active",
            created_at=datetime.now(),
            referral_code=referral_code,
            referred_by_id=referred_by
        )

        db.session.add(new_user)
        db.session.flush()  # get new_user.id

        new_customer = Customer(
            user_id=new_user.id,
            username=new_user.username,
            first_name=first_name,
            last_name=last_name,
            email=email
        )
        db.session.add(new_customer)

        # Generate verification code before commit
        code = secrets.token_hex(4).upper()
        new_user.password_reset_token = code
        new_user.token_created_at = datetime.now()

        # Log activity BEFORE commit, inside transaction
        log_activity(status_code=200,  ip_address=request.remote_addr, user_id=new_user.id, event_message="Account created.")

        db.session.commit()

        session.clear()
        session["user_id"] = new_user.id

        logger.info("User and customer created successfully for username: %s", username)
        return jsonify(success=True)

    
    except Exception as e:
        app.logger.exception(f"[AUTH] Unexpected error while signing up user {new_user.username}")
        return jsonify(success=False, message="Internal server error"), 500

    except Exception as e:
        db.session.rollback()
        logger.error("Signup error for %s: %s", username, e, exc_info=True)
        errors['general'] = "An unexpected error occurred. Please try again later."
        return jsonify(success=False, errors=errors, form_data=form_data), 500

@general_bp.route("/referrals/code", methods=["GET"])
def get_referral_code():
    try:
        try:
            user_id = authorizeUser()
            if not user_id :
                logger.warning("Unauthorized access attempt by user_id=%s", user_id)
                return jsonify({"error": "Unauthorized access"}), 403
        except Exception as e:
            logger.error("User not authorized: %s", e, exc_info=True)
            return jsonify({"error": "Unauthorized"}), 403
        
        user = db.session.get(User, user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({"referral_code": user.referral_code}), 200

    except Exception as e:
        logger.error(f"Error fetching referral code: {e}", exc_info=True)
        return jsonify({"error": "Failed to retrieve referral code"}), 500

@general_bp.route("/referrals/send", methods=["POST"]) # DEBUG MODAL ADDED REMOVE LATER
@csrf.exempt
def send_referral_email():
    try:
        user_id = authorizeUser()
        data = request.get_json()
        recipient_email = data.get("email")

        if not recipient_email:
            return jsonify({"error": "Email is required"}), 400

        try:
            if not user_id:
                logger.warning("Unauthorized access attempt by user_id=%s", user_id)
                return jsonify({"error": "Unauthorized access"}), 403
        except Exception as e:
            logger.error("Session error in test_hypervisor_status: %s", e, exc_info=True)
            return jsonify({"error": "Unauthorized"}), 403
        
        referrer = db.session.get(User, user_id)

        if not referrer:
            return jsonify({"error": "User not found"}), 404
        
        # Validate email
        if not recipient_email:
            return jsonify({"error": "Invalid or undeliverable email."}), 400
        
        # Award if user sends to themselves
        if recipient_email.lower() == referrer.customer.email.lower():
            award_badge_by_name(referrer, "Solo Sales Team")
            return jsonify({"error": "Bold move trying to refer yourself. We admire the hustle, but self-referrals don't count. Try making a friend instead."}), 400

        # Award first-time referral
        def has_sent_any_referrals(user_id):
            return db.session.query(Referral).filter_by(referrer_id=user_id).count() > 0
        if not has_sent_any_referrals(referrer.id):
            award_badge_by_name(referrer, "First Referral Sent")

        # Award for trying to refer the same person
        existing = db.session.query(Referral).filter_by(
            referrer_id=referrer.id,
            recipient_email=recipient_email
        ).first()
        if existing:
            # Award badge for trying to refer same person
            award_badge_by_name(referrer, "Spammy McSpammerson")
            return jsonify({"error": "Whoa there, social butterfly - You already shot your shot with this email. Don't make it weird."}), 400


        ip_address = request.remote_addr
        send_referral_invitation_email(
            subject="🔥 You've been invited to Carpathian Cloud!",
            recipient_email=recipient_email,
            referrer=referrer,
            ip_address=ip_address
        )

        logger.info(f"Referral email sent from {referrer.username} to {recipient_email}")
        return jsonify({"message": "Referral email sent"}), 200

    except Exception as e:
        logger.error(f"Error sending referral email: {e}", exc_info=True)
        return jsonify({"error": "Failed to send referral email"}), 500

@general_bp.route("/badges/earned", methods=["GET"])
def get_earned_badges():
    user_id = authorizeUser()
    logger.info(f"Fetching earned badges for user_id={user_id}")

    try:
        # Join EarnedBadge with BadgeDefinition
        results = (
            db.session.query(EarnedBadge, BadgeDefinition)
            .join(BadgeDefinition, EarnedBadge.badge_id == BadgeDefinition.id)
            .filter(EarnedBadge.user_id == user_id)
            .order_by(desc(EarnedBadge.earned_on))
            .all()
        )

        logger.info(f"Found {len(results)} earned badges for user_id={user_id}")

        serialized_badges = [
            {
                "id": badge.id,
                "badge_name": badge.name,
                "description": badge.description,
                "icon_url": badge.icon_url,
                "category": badge.category,
                "earned_on": earned.earned_on.isoformat() if earned.earned_on else None
            }
            for earned, badge in results
        ]

        return jsonify(serialized_badges), 200

    except Exception as e:
        logger.error(f"Error retrieving earned badges for user_id={user_id}: {e}", exc_info=True)
        return jsonify({"error": "Could not retrieve badges."}), 500

@general_bp.route("/badges/definitions", methods=["GET"])
def get_badge_definitions():
    user_id = authorizeUser()
    logger.info(f"[get_badge_definitions] start – user_id={user_id}")
    start_ts = time.time()
    try:
        defs = BadgeDefinition.query.order_by(BadgeDefinition.name).all()
        logger.debug(f"[get_badge_definitions] query returned {len(defs)} rows")
        
        serialized = []
        for d in defs:
            serialized.append({
                "id":          d.id,
                "name":        d.name,
                "description": d.description,
                "icon_url":    d.icon_url
            })
        logger.info(f"[get_badge_definitions] serialized {len(serialized)} definitions for user {user_id}")
        
        duration = (time.time() - start_ts) * 1000
        logger.info(f"[get_badge_definitions] success – duration={duration:.1f}ms")
        return jsonify(serialized), 200

    except Exception:
        logger.exception(f"[get_badge_definitions] failure for user {user_id}")
        return jsonify({"error": "Could not load badge definitions."}), 500
    
@general_bp.route("/meta/version", methods=["GET"])
def version_info():
    def parse_items(raw_text):
        lines = [line.strip() for line in raw_text.strip().split("\n") if line.strip()]
        items = []
        for line in lines:
            if line.startswith("*"):
                title = line.lstrip("* ").strip()
                description = ""
            elif ":" in line:
                title, description = line.split(":", 1)
                title = title.strip()
                description = description.strip()
            else:
                title = line
                description = ""
            items.append({
                "id": str(uuid.uuid4()),
                "title": title,
                "description": description
            })
        return items
    version_type = request.args.get("type", "all").lower()


    if version_type == "backend":
        return jsonify({"backend_version": BACKEND_VERSION})
    elif version_type == "frontend":
        return jsonify({"frontend_version": FRONTEND_VERSION})

    return jsonify({
        "backend_version": BACKEND_VERSION,
        "frontend_version": FRONTEND_VERSION,
    })

@general_bp.route("/settings/notifications", methods=["GET", "POST", "DELETE"])
@csrf.exempt
def manage_notifications():
    user_id = authorizeUser()
    logger.info(f"User {user_id} is attempting to manage system_notifications")

    # --- LIST ---
    if request.method == "GET":
        all_notifs = Notification.query.all()
        return jsonify({
            "notifications": [
                {
                    "location": n.display_location.value,
                    "message": n.message,
                    "severity": n.severity,
                    "created_at": n.created_at.isoformat(),
                    "updated_at": n.updated_at.isoformat(),
                }
                for n in all_notifs
            ]
        }), 200

    data = request.get_json() or {}
    loc = data.get("location")
    if not loc:
        return jsonify({"error": "location is required"}), 400

    try:
        loc_enum = NotificationLocation(loc)
    except ValueError:
        return jsonify({"error": "Invalid location"}), 400

    # --- CREATE / UPDATE ---
    if request.method == "POST":
        msg = data.get("message", "").strip()
        if not msg:
            return jsonify({"error": "message is required"}), 400

        severity = int(data.get("severity", 0))

        existing = Notification.query.filter_by(display_location=loc_enum).first()
        if existing:
            existing.message = msg
            existing.severity = severity
        else:
            new_notif = Notification(
                display_location=loc_enum,
                message=msg,
                severity=severity
            )
            db.session.add(new_notif)

        db.session.commit()
        return jsonify({"success": True}), 201

    # --- DELETE ---
    if request.method == "DELETE":
        existing = Notification.query.filter_by(display_location=loc_enum).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
        return jsonify({"success": True}), 200

@general_bp.route("/notifications/<string:location>", methods=["GET"])
def get_notification(location):
    # public, read-only
    try:
        loc_enum = NotificationLocation(location)
    except ValueError:
        return jsonify({"message": None}), 404

    notif = Notification.query.filter_by(display_location=loc_enum).first()
    if notif:
        return jsonify({
            "message": notif.message,
            "severity": notif.severity
        }), 200

    return jsonify({"message": None}), 200
