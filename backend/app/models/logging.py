# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Authorized.
# ------------------------------------------------------------------------------------
# Notes:
# - Logging and record keeping

# ------------------------------------------------------------------------------------
# Imports:
from datetime import datetime

# Local Imports
from app.extensions import db

# ------------------------------------------------------------------------------------
# Var Decs

# ------------------------------------------------------------------------------------
# Classes

# AccessLog 
class ActivityLog(db.Model):
    __tablename__ = 'activity_log'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ip_address = db.Column(db.String(45), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    guest_id = db.Column(db.String(255), db.ForeignKey('guest_users.guest_id', ondelete='SET NULL'), nullable=True)
    session_id = db.Column(db.String(255), nullable=True)
    path = db.Column(db.String(255), nullable=True)
    method = db.Column(db.String(10), nullable=True)
    status_code = db.Column(db.Integer, nullable=False)
    accessed_at = db.Column(db.DateTime, default=datetime.now())
    query_params = db.Column(db.Text, nullable=True)
    referrer = db.Column(db.String(255), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    app_version = db.Column(db.String(50), nullable=True)
    response_time = db.Column(db.Float, nullable=True)
    country = db.Column(db.String(50), nullable=True)
    region = db.Column(db.String(50), nullable=True)
    city = db.Column(db.String(50), nullable=True)
    device_type = db.Column(db.String(50), nullable=True)
    browser_name = db.Column(db.String(50), nullable=True)
    os_name = db.Column(db.String(50), nullable=True)
    event_message = db.Column(db.Text, nullable=True)

    # Relationships
    user = db.relationship('User', backref='access_logs')
    guest_user = db.relationship('GuestUser', backref='access_logs')

    def __repr__(self):
        return f"<AccessLog(id={self.id}, ip_address='{self.ip_address}', path='{self.path}', status_code={self.status_code})>"

class UserActivityLog(db.Model):
    __tablename__ = "user_activity_log"

    id            = db.Column(db.Integer, primary_key=True)
    timestamp     = db.Column(db.DateTime, default=datetime.now, nullable=False)
    user_id       = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ip_address    = db.Column(db.String(45), nullable=False)
    path          = db.Column(db.String(255), nullable=False)
    method        = db.Column(db.String(10), nullable=False)
    status_code   = db.Column(db.Integer, nullable=False)
    response_time = db.Column(db.Float, nullable=True)
    user_agent    = db.Column(db.Text, nullable=True)
    device_type   = db.Column(db.String(50), nullable=True)
    browser_name  = db.Column(db.String(50), nullable=True)
    os_name       = db.Column(db.String(50), nullable=True)
    event_message = db.Column(db.Text, nullable=True)
    metadata_json = db.Column(db.JSON, nullable=True)

class SiteSecurityLog(db.Model):
    __tablename__ = "site_security_log"

    id            = db.Column(db.Integer, primary_key=True)
    timestamp     = db.Column(db.DateTime, default=datetime.now, nullable=False)
    ip_address    = db.Column(db.String(45), nullable=False)
    user_id       = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    guest_id      = db.Column(db.String(255), nullable=True)
    event_type    = db.Column(db.String(50), nullable=False)
    event_message = db.Column(db.Text, nullable=True)
    path          = db.Column(db.String(255), nullable=True)
    method        = db.Column(db.String(10), nullable=True)
    status_code   = db.Column(db.Integer, nullable=True)
    user_agent    = db.Column(db.Text, nullable=True)
    metadata_json      = db.Column(db.JSON, nullable=True)

class HoneypotLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45))
    session_id = db.Column(db.String(256), nullable=True)
    path = db.Column(db.String(200))
    method = db.Column(db.String(10))
    status_code = db.Column(db.Integer)
    query_params = db.Column(db.Text)
    referrer = db.Column(db.String(300))
    user_agent = db.Column(db.String(500))
    app_version = db.Column(db.String(50))
    response_time = db.Column(db.Float, nullable=True)
    country = db.Column(db.String(100))
    region = db.Column(db.String(100))
    city = db.Column(db.String(100))
    device_type = db.Column(db.String(50))
    browser_name = db.Column(db.String(50))
    os_name = db.Column(db.String(50))
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now())

class FailedLoginAttempt(db.Model):
    __tablename__ = 'failed_login_attempt'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ip_address = db.Column(db.String(45), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now(), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Relationship
    user = db.relationship('User', back_populates='failed_login_attempts')

    def __repr__(self):
        return f"<FailedLoginAttempt(id={self.id}, ip_address='{self.ip_address}', timestamp='{self.timestamp}')>"

class HealthLog(db.Model):
    __tablename__ = "health_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    resolved_by   = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    severity    = db.Column(db.Enum("info", "warning", "critical", name="severity_enum"), nullable=False, default="info")
    issue_type  = db.Column(db.String(100), nullable=True)  # e.g., "disk", "memory"
    message     = db.Column(db.Text, nullable=False)
    resolved    = db.Column(db.Boolean, default=False)
    timestamp   = db.Column(db.DateTime, default=datetime.now)
    resolved_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    resolver = db.relationship("User", back_populates="resolved_issues", foreign_keys=[resolved_by])


    def __repr__(self):
        return f"<HealthLog id={self.id} severity={self.severity} type={self.issue_type}>"
