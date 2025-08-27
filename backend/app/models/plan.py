# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# Notes:
# - All classes related to plans and packages (small for now but will make future mngt easier and centralized)

# ------------------------------------------------------------------------------------
# Imports:
from datetime import datetime

# Local Imports
from app.extensions import db

# ------------------------------------------------------------------------------------
# Var Decs

# ------------------------------------------------------------------------------------
# Classes

class Plan(db.Model):
    __tablename__ = 'plans'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(
        db.Enum(
            "unregistered",
            "registered",
            "starter",
            "growth",
            "professional",
            "enterprise",
            "infinite",
            name="plan_names"
        ),
        nullable=False,
        unique=True
    )
    price = db.Column(db.Integer, default=0)
    stripe_price_id = db.Column(db.String(100))
    stripe_product_id = db.Column(db.String(100))
    description = db.Column(db.String(255))
    support_level = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    users = db.relationship("User", back_populates="plan", passive_deletes=True)
    guest_users = db.relationship("GuestUser", back_populates="plan")


    def __repr__(self):
        return f"<Plan(id={self.id}, name='{self.name}')>"
