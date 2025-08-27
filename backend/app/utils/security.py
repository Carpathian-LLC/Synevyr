# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# Notes:
# - All general helper functions

# ------------------------------------------------------------------------------------
# Imports:
from flask import session, request

# Local Imports
from app.utils.logging import logger, unauthorized_logger
from app.extensions import db
from app.models.user import User

# ------------------------------------------------------------------------------------
# Var Decs

# ------------------------------------------------------------------------------------
# Functions

# Master Auth Helper Function
def authorizeUser(required_roles=None, required_permissions=None):
    try:
        user_id = session.get("user_id")

        if not user_id:
            unauthorized_logger.warning(
                f"Unauthorized access: No session found. "
                f"IP={request.remote_addr}, Path={request.path}, Method={request.method}, user_id=None"
            )
            raise PermissionError("Unauthorized")

        user = db.session.get(User, user_id)
        if not user:
            unauthorized_logger.warning(
                f"Unauthorized access: User not found in DB. "
                f"IP={request.remote_addr}, Path={request.path}, Method={request.method}, user_id={user_id}"
            )
            raise PermissionError("Unauthorized")

        return user_id

    except Exception as e:
        logger.error("Authorization failure: %s", e, exc_info=True)
        raise PermissionError("Unauthorized")