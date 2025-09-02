# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# Description:
# Centralized table creation utility using SQLAlchemy models as the single source of truth
# ------------------------------------------------------------------------------------

from sqlalchemy import create_engine
from app.extensions import db

# Import all models to ensure they're registered
from app.models.user import User, Customer
from app.models.plan import Plan
from app.models.analysis import CustomerAnalysis, CustomerStats, SourceMetricsDaily
from app.models.data_sources import DataSource, UserDatasetRaw, AnalyticsEtlState
from app.models.logging import ActivityLog, UserActivityLog, SiteSecurityLog, FailedLoginAttempt
from app.models.public_data import Leads, WooCommerceOrder, UserCustomer
def create_all_tables(engine=None):
    """
    Creates all tables defined in SQLAlchemy models.
    This is the single source of truth for table structure.
    """
    if engine:
        # Use provided engine (for standalone scripts)
        try:
            # Create minimal Flask app context for SQLAlchemy
            from flask import Flask
            app = Flask(__name__)
            app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://placeholder"
            app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
            
            with app.app_context():
                db.metadata.create_all(bind=engine)
        except Exception as e:
            print(f"Error creating tables with Flask app context: {e}")
            raise
    else:
        # Use app context (for Flask app initialization)
        db.create_all()

def get_table_creation_sql(engine):
    """
    Returns the SQL statements that would create all tables.
    Useful for debugging or generating migration scripts.
    """
    from sqlalchemy.schema import CreateTable
    
    sql_statements = []
    for table in db.metadata.tables.values():
        sql_statements.append(str(CreateTable(table).compile(engine)))
    
    return sql_statements

def drop_all_tables(engine=None):
    """
    Drops all tables. Use with caution!
    """
    if engine:
        db.metadata.drop_all(bind=engine)
    else:
        db.drop_all()