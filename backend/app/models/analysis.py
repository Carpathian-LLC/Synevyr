# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Authorized.
# ------------------------------------------------------------------------------------
# Notes:
# - classes related to user management
# ------------------------------------------------------------------------------------
# Imports:
from datetime import datetime

# Local Imports
from app.extensions import db
# ------------------------------------------------------------------------------------
# Var Decs

# ------------------------------------------------------------------------------------
# Classes

class Customer(db.Model):
    __tablename__ = 'user_customers'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)

    # Required fields from table
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(255), nullable=True)
    state = db.Column(db.String(255), nullable=True)
    country = db.Column(db.String(255), nullable=True)
    zipcode = db.Column(db.String(255), nullable=True)
    activity_status = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.Date, nullable=False)
    referrer = db.Column(db.String(255), nullable=True)

    # Stripe and user linkage (optional)
    stripe_customer_id = db.Column(db.String(255), nullable=True)
    stripe_subscription_id = db.Column(db.String(255), nullable=True)
    stripe_captured_email = db.Column(db.String(255), nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    username = db.Column(db.String(80), unique=True, nullable=True)

    user = db.relationship('User', back_populates='customer')

    def __repr__(self):
        return f"<Customer(id={self.id}, email='{self.email}')>"
