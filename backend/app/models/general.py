# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# Notes:
# - Misc classes (not sure where to place them yet)

# Add new system notification locations here
# ------------------------------------------------------------------------------------
# Imports:
from datetime import datetime
import enum
from app.extensions import db

# ------------------------------------------------------------------------------------
# Var Decs

# ------------------------------------------------------------------------------------
# Classes

class BadgeDefinition(db.Model):
    __tablename__ = "badge_definitions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    icon_url = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.Text, nullable=True)

class EarnedBadge(db.Model):
    __tablename__ = "earned_badges"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey("badge_definitions.id", ondelete="CASCADE"), nullable=False)
    earned_on = db.Column(db.DateTime, default=datetime.now, nullable=False)

    user = db.relationship("User", backref=db.backref("earned_badges", lazy="dynamic"))
    badge = db.relationship("BadgeDefinition", backref="earned_by")

    __table_args__ = (db.UniqueConstraint('user_id', 'badge_id', name='_user_badge_uc'),)

# ADD NEW NOTIFICATION LOCATIONS HERE
class NotificationLocation(enum.Enum):
    LOGIN = "login"
    DASHBOARD = "dashboard"
    SIGNUP = "signup"
    # add new locations here as needed, e.g. DASHBOARD = "dashboard"

class Notification(db.Model):
    __tablename__ = "system_notifications"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )
    display_location = db.Column(
        db.Enum(NotificationLocation),
        unique=True,
        nullable=False
    )
    message = db.Column(
        db.Text,
        nullable=False
    )
    severity = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now
    )

    def __repr__(self):
        loc = self.display_location.value if isinstance(self.display_location, NotificationLocation) else self.display_location
        return f"<Notification {loc}: {self.message[:20]}…>"

class ActionLock(db.Model):
    # Used for debugging race conditions
    __tablename__ = "action_locks"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action_type = db.Column(db.String(100), nullable=False)
    action_token = db.Column(db.String(255), nullable=False, unique=True)
    state = db.Column(db.Enum("locked", "released", "failed", name="lock_state"), default="locked", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    released_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", backref=db.backref("action_locks", lazy=True))

    def __repr__(self):
        return f"<ActionLock {self.action_type} for user {self.user_id} | {self.state}>"
