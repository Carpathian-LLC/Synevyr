# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# 🏢 PLATFORM MODELS - Synevyr System Users & Customers
# ------------------------------------------------------------------------------------
# These models represent Synevyr's platform users (people who use the Synevyr app)
# and platform customers (people who pay for Synevyr subscriptions).
# 
# NOT to be confused with demo data models (crm_customers, etc.) which represent
# synthetic demo customer data used for testing platform functionality.
#
# Platform Models in this file:
# - User: Synevyr platform users (login accounts)
# - GuestUser: Anonymous visitors to Synevyr
# - Customer: Synevyr paying customers (Stripe integration)
# - Referral: Platform referral system
# ------------------------------------------------------------------------------------

# ------------------------------------------------------------------------------------
# Imports:
from datetime import datetime
from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Local Imports
from app.extensions import db

# ------------------------------------------------------------------------------------
# Var Decs

# ------------------------------------------------------------------------------------
# Classes
class BaseUser:
    @property
    def is_authenticated(self):
        return False

class User(UserMixin, BaseUser, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    two_fa_enabled  = db.Column(db.Boolean, nullable=True)
    totp_secret = db.Column(db.String(255), nullable=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("plans.id", ondelete="SET NULL"), nullable=True)
    status = db.Column(
        db.Enum('active', 'inactive', 'suspended', 'unverified'),
        default='unverified',
        nullable=False
    )
    trust_level = db.Column(db.Enum('0', '1', '2', '3', '10'), default='0', nullable=False)
    last_reset_date = db.Column(db.Date, nullable=True)
    failed_attempts = db.Column(db.Integer, default=0)
    last_failed_login = db.Column(db.DateTime, nullable=True)
    last_successful_login = db.Column(db.DateTime, nullable=True)
    last_login_ip = db.Column(db.String(20), nullable=True)
    is_suspended = db.Column(db.Boolean, default=False)
    suspension_end = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, default=datetime.now(), onupdate=datetime.now())
    last_password_reset = db.Column(db.DateTime, nullable=True)
    password_reset_token = db.Column(db.String(255), nullable=True)
    token_created_at = db.Column(db.DateTime, nullable=True)
    
    referral_code = db.Column(db.String(64), unique=True)
    referred_by_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Relationships
    plan = db.relationship('Plan', back_populates='users')
    customer = db.relationship('Customer', back_populates='user', uselist=False)
    failed_login_attempts = db.relationship('FailedLoginAttempt', back_populates='user', cascade="all, delete-orphan")
    guest_users = db.relationship('GuestUser', back_populates='owner_user', cascade="all, delete-orphan")
    api_keys = db.relationship('UserApiKey', back_populates='user', cascade="all, delete-orphan")
    referred_by = db.relationship('User', remote_side=[id], backref='referrals_sent', foreign_keys=[referred_by_id],passive_deletes=True,)
    resolved_issues = db.relationship("HealthLog", back_populates="resolver", foreign_keys="HealthLog.resolved_by")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"

    @property
    def full_name(self):
        if not self.customer:
            return None
        first = self.customer.first_name or ""
        last = self.customer.last_name or ""
        return f"{first} {last}".strip() or None
    
    # (Add password and storage utility methods as needed)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
 
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "plan": self.plan.to_dict() if self.plan else None,
            "status": self.status,
            "trust_level": self.trust_level,
            "last_login_ip": self.last_login_ip,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

# GuestUser 
class GuestUser(AnonymousUserMixin, BaseUser, db.Model):
    __tablename__ = 'guest_users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    guest_id = db.Column(db.String(255), unique=True, nullable=False)
    owner_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    short_code = db.Column(db.String(6), unique=True, nullable=True)
    ip_address = db.Column(db.String(45), nullable=False)
    last_reset_date = db.Column(db.Date, nullable=True)
    redirect_url = db.Column(db.String(255), nullable=True)
    is_authenticated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now())
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), default='active')
    first_seen     = db.Column(db.DateTime, default=datetime.now, nullable=False)
    last_seen      = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    visit_count    = db.Column(db.Integer, default=0, nullable=False)
    session_count  = db.Column(db.Integer, default=0, nullable=False)
    user_agent     = db.Column(db.Text, nullable=True)
    referrer       = db.Column(db.String(2048), nullable=True)
    metadata_json  = db.Column(db.JSON, nullable=True)

    # Relationships
    plan = db.relationship('Plan', back_populates='guest_users')
    owner_user = db.relationship('User', back_populates='guest_users')

    def __repr__(self):
        return f"<GuestUser(id={self.id}, guest_id='{self.guest_id}')>"

    def to_dict(self):
        return {
            "id": self.id,
            "guest_id": self.guest_id,
            "owner_user_id": self.owner_user_id,
            "ip_address": self.ip_address,
            "plan": self.plan.to_dict() if self.plan else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

# Customer 
class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stripe_customer_id = db.Column(db.String(255), nullable=True)
    stripe_subscription_id = db.Column(db.String(255), nullable=True)
    stripe_captured_email = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(15), nullable=True)

    # Relationship
    user = db.relationship('User', back_populates='customer')

    def __repr__(self):
        return f"<Customer(id={self.id}, email='{self.email}')>"

class Referral(db.Model):
    __tablename__ = "referrals"

    id = db.Column(db.Integer, primary_key=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recipient_email = db.Column(db.String(255), nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    referrer = db.relationship("User", backref=db.backref("referral_emails_sent", lazy="dynamic"))

    def __repr__(self):
        return f"<Referral to={self.recipient_email} from={self.referrer_id}>"

class UserApiKey(db.Model):
    __tablename__ = 'user_api_key'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    api_key = db.Column(db.String(255), unique=True, nullable=False)
    hashed_api_key = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, default=datetime.now(), onupdate=datetime.now())

    # Relationships
    user = db.relationship('User', back_populates='api_keys')

    def __repr__(self):
        return f"<UserApiKey(id={self.id}, api_key='{self.api_key}')>"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "api_key": self.api_key,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }