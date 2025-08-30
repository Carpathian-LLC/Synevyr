#------------------------------------------------------------------------------------
# Developed by Carpathian, LLC. 
#------------------------------------------------------------------------------------

mk_database_version = "1.0"

#------------------------------------CHANGES-----------------------------------------
# 1.0 - Initial refactor.

#------------------------------------IMPORTS-----------------------------------------

import os
from pathlib import Path
from dotenv import load_dotenv
import mysql.connector 

#------------------------------------------------------------------------------------
# Env Load
env_path = Path(__file__).resolve().parents[2] / "keys.env"

if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    print("✓ Loaded .env:", env_path)
else:
    print("✗ keys.env not found at", env_path)

DEFAULT_PLANS = [
    {
        "name": "unregistered",
    },
    {
        "name": "registered",
    },
]
#------------------------------------------------------------------------------------
# Functions

def connect_to_remote_database(db_environment):
    """Establishes a secure connection to the remote MySQL server and switches to the 'db_synevyr' database."""
    try:
        print("Attempting to connect to the remote MySQL server...")

        # Connect to 'mysql' database initially
        connection = mysql.connector.connect(
            host=os.getenv("REMOTE_DB_HOST"),
            user=os.getenv("REMOTE_DB_USER"),
            password=os.getenv("REMOTE_DB_PASSWORD"),
            database="mysql",  # Start with 'mysql'
            port=int(os.getenv("REMOTE_DB_PORT", 3306)),
            ssl_ca=os.getenv("MYSQL_SSL_CA"),
            ssl_cert=os.getenv("MYSQL_SSL_CERT"),
            ssl_key=os.getenv("MYSQL_SSL_KEY"),
            ssl_verify_cert=True
        )
        print("Connected to remote MySQL server.")

        # Ensure 'db_synevyr' database exists
        db_name = os.getenv("DATABASE", "db_synevyr")
        cursor = connection.cursor()
        cursor.execute(f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{db_name}'")
        result = cursor.fetchone()

        if result:
            print(f"Database '{db_name}' already exists. Switching to it.")
        else:
            print(f"Database '{db_name}' does not exist. Creating it now...")
            cursor.execute(f"CREATE DATABASE {db_name}")

        # Switch to the 'db_synevyr' database
        cursor.execute(f"USE {db_name}")
        print(f"Using database: {db_name}")

        return connection

    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")
        raise
    except Exception as e:
        print(f"General Error: {e}")
        raise

def connect_to_local_database(db_environment): 
    """Connects to the local MySQL server and switches to the 'db_synevyr' database."""
    try:
        # Connect to 'mysql' database initially
        connection = mysql.connector.connect(
            host=os.getenv(f"{db_environment.upper()}_DB_HOST", "localhost"),
            user=os.getenv(f"{db_environment.upper()}_DB_USER"),
            password=os.getenv(f"{db_environment.upper()}_DB_PASSWORD", ""),
            database="mysql",  # Start with 'mysql'
            port=int(os.getenv(f"{db_environment.upper()}_DB_PORT", 3306))
        )
        print("Connected to local MySQL server.")

        # Ensure 'db_synevyr' database exists
        
        db_name = os.getenv(f"DATABASE", "db_synevyr")
        cursor = connection.cursor()
        cursor.execute(f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{db_name}'")
        result = cursor.fetchone()

        if result:
            print(f"Database '{db_name}' already exists. Switching to it.")
        else:
            print(f"Database '{db_name}' does not exist. Creating it now...")
            cursor.execute(f"CREATE DATABASE {db_name}")

        # Switch to the 'db_synevyr' database
        cursor.execute(f"USE {db_name}")
        print(f"Using database: {db_name}")

        return connection

    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")
        raise

def get_sqlalchemy_database_uri(db_environment):
    # Map "dev" to "development" for backwards compatibility
    if db_environment == "dev":
        db_environment = "development"
    
    db_config = {
        "demo": {
            "user": os.getenv("DEMO_DB_USER"),
            "password": os.getenv("DEMO_DB_PASSWORD"),
            "host": os.getenv("DEMO_DB_HOST", "localhost"),
            "port": os.getenv("DEMO_DB_PORT", "3306"),
            "database": os.getenv("DATABASE", "")
        },
        "development": {
            "user": os.getenv("DEV_DB_USER"),
            "password": os.getenv("DEV_DB_PASSWORD"),
            "host": os.getenv("DEV_DB_HOST", "localhost"),
            "port": os.getenv("DEV_DB_PORT", "3306"),
            "database": os.getenv("DATABASE", "")
        },
        "production": {
            "user": os.getenv("PROD_DB_USER"),
            "password": os.getenv("PROD_DB_PASSWORD"),
            "host": os.getenv("PROD_DB_HOST", "localhost"),
            "port": os.getenv("PROD_DB_PORT", "3306"),
            "database": os.getenv("DATABASE", "")
        },
    }.get(db_environment)

    if not db_config:
        raise ValueError("Invalid database environment specified.")

    return (
        "mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
        "?ssl_verify_cert=false"
    ).format(**db_config)

def ensure_connection(connection):
    """Ensures the connection to the database is active. Reconnects if disconnected."""
    try:
        if not connection.is_connected():
            print("Connection lost. Attempting to reconnect...")
            connection.reconnect(attempts=3, delay=5)
            print("Reconnected successfully.")
    except mysql.connector.Error as e:
        print(f"Failed to reconnect to MySQL: {e}")
        raise

def close_connection(connection, cursor=None):
    """Closes the cursor and database connection safely."""
    try:
        if cursor:
            cursor.close()
        if connection.is_connected():
            connection.close()
            print("Database connection closed.")
    except mysql.connector.Error as err:
        print(f"Error closing connection: {err}")

def preload_all_data(cursor):
    # === 1. Seed Plans === 
    cursor.execute("SELECT name FROM plans")
    existing_plans = {row[0] for row in cursor.fetchall()}
    for plan in DEFAULT_PLANS:
        if plan["name"] not in existing_plans:
            def fmt(val):
                return "NULL" if val is None else str(val)
            cursor.execute(
                f"""
                INSERT INTO plans (name, created_at)
                VALUES ('{plan["name"]}', CURRENT_TIMESTAMP)
                """
            )

    print("✅ All default data seeded successfully.")

def create_database_and_tables(connection, db_environment):
    """Creates the necessary database and tables using centralized SQLAlchemy models."""
    cursor = connection.cursor()
    try:
        # Step 1: Start with the mysql database
        cursor.execute("USE mysql")

        # Step 2: Check if the 'db_synevyr' database exists
        db_name = os.getenv("DATABASE", 'db_synevyr')  # Use DATABASE env var or default
        cursor.execute(f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{db_name}'")
        result = cursor.fetchone()

        # Step 3: If the database doesn't exist, create it
        if not result:
            print(f"Database '{db_name}' does not exist. Creating it now...")
            cursor.execute(f"CREATE DATABASE {db_name}")
        else:
            print(f"Database '{db_name}' already exists.")

        # Step 4: Switch to the target database
        cursor.execute(f"USE {db_name}")
        print(f"Using database: {db_name}")

        # Step 5: Create all tables using centralized SQLAlchemy models
        print("Creating all tables using centralized SQLAlchemy models...")
        
        # Import SQLAlchemy engine and centralized table creation utility
        from sqlalchemy import create_engine
        from .create_tables import create_all_tables
        
        # Build database URI for SQLAlchemy
        db_uri = get_sqlalchemy_database_uri(db_environment.lower())
        engine = create_engine(db_uri)
        
        # Use centralized table creation
        create_all_tables(engine)
        print("✅ All tables created using SQLAlchemy models.")

        # Seed default data
        preload_all_data(cursor)

        connection.commit()
    finally:
        close_connection(connection, cursor)

#------------------------------------MAIN EXECUTION----------------------------------

def initialize_database(db_environment):
    """Initializes the database and tables based on DB_MODE environment setting."""
    db_mode = os.getenv("DB_MODE", "local")
    if db_mode == "remote":
        print("Connecting to remote DB")
        connection = connect_to_remote_database(db_environment)
    else:
        print("Connecting to local DB")
        connection = connect_to_local_database(db_environment)
    
    create_database_and_tables(connection, db_environment)

