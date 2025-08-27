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
    """Creates the necessary database and tables if they do not exist."""
    cursor = connection.cursor()
    try:
        # Step 1: Start with the mysql database
        cursor.execute("USE mysql")

        # Step 2: Check if the 'db_synevyr' database exists
        db_name = os.getenv(db_environment, 'db_synevyr')  # Default to 'db_synevyr' if not specified
        cursor.execute(f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{db_name}'")
        result = cursor.fetchone()

        # Step 3: If the database doesn't exist, create it
        if not result:
            print(f"Database '{db_name}' does not exist. Creating it now...")
            cursor.execute(f"CREATE DATABASE {db_name}")
        else:
            print(f"Database '{db_name}' already exists.")

        # Step 4: Switch to the db_synevyr database
        cursor.execute(f"USE {db_name}")
        print(f"Using database: {db_name}")

        # Create database if it does not exist
        cursor.execute("USE mysql")
        cursor.execute("CREATE DATABASE IF NOT EXISTS db_synevyr")
        cursor.execute("USE db_synevyr")

        # Primary Table for the CLOUD aspect of the platform. These are the
        # tables that Synevyr uses to keep track of our customers.

        #Plans (Profiles) Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS plans (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name ENUM('unregistered', 'registered', 'starter', 'growth', 'professional', 'enterprise', 'infinite') NOT NULL UNIQUE,
            price INT DEFAULT 0,
            support_level VARCHAR(100),
            stripe_price_id VARCHAR(100),
            stripe_product_id VARCHAR(100),
            description VARCHAR(255),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # USERS table
        cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(80) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    two_fa_enabled TINYINT(1),
                    totp_secret VARCHAR(255),
                    plan_id INT NULL,
                    status ENUM('active', 'inactive', 'suspended', 'unverified', 'owner') DEFAULT 'unverified',
                    trust_level ENUM('0','1','2','3', '10') DEFAULT '0',
                    last_reset_date DATE,
                    failed_attempts INT DEFAULT 0,
                    last_failed_login TIMESTAMP NULL,
                    last_successful_login TIMESTAMP NULL,
                    last_login_ip VARCHAR(20),
                    is_suspended BOOLEAN DEFAULT FALSE,
                    suspension_end TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    last_password_reset TIMESTAMP,
                    password_reset_token VARCHAR(255),
                    token_created_at DATETIME,
                    referral_code VARCHAR(64) UNIQUE,
                    referred_by_id INT NULL,
                    FOREIGN KEY (plan_id) REFERENCES plans(id) ON DELETE SET NULL,
                    FOREIGN KEY (referred_by_id) REFERENCES users(id) ON DELETE SET NULL
                );
                """)


        # GUEST_USERS table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS guest_users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            guest_id VARCHAR(255) NOT NULL UNIQUE,
            owner_user_id INT NULL,
            short_code VARCHAR(6) UNIQUE,
            ip_address VARCHAR(45) NOT NULL,
            last_reset_date DATE,
            redirect_url VARCHAR(255) NULL,
            is_authenticated BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            plan_id INT NOT NULL,
            first_seen   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_seen    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            visit_count  INT          NOT NULL DEFAULT 0,
            session_count INT         NOT NULL DEFAULT 0,
            user_agent   TEXT         NULL,
            referrer     VARCHAR(2048) NULL,
            metadata_json     JSON         NULL,
            status VARCHAR(20) DEFAULT 'active',
            FOREIGN KEY (plan_id) REFERENCES plans(id) ON DELETE CASCADE,
            FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """)

        # CUSTOMERS table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            stripe_customer_id VARCHAR(255),
            stripe_subscription_id VARCHAR(255),
            stripe_captured_email VARCHAR(255),
            email VARCHAR(120) NOT NULL UNIQUE,
            user_id INT NOT NULL, 
            username VARCHAR(80) UNIQUE NOT NULL,
            first_name VARCHAR(80) NOT NULL,
            last_name VARCHAR(80) NOT NULL,
            phone VARCHAR(15),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """)


        cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_sources (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL,
            source_type VARCHAR(32) NOT NULL DEFAULT 'api',  -- 'api' | 'manual' | 'file' (expand later)
            name VARCHAR(255) NOT NULL,
            base_url TEXT NULL,                               -- nullable for non-API sources
            api_key TEXT NULL,
            config JSON NULL,                                 -- optional key-value metadata
            notes TEXT NULL,                                  -- user notes
            last_updated DATETIME NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uq_data_sources_user_name (user_id, name),
            INDEX idx_data_sources_last_updated (last_updated),
            CONSTRAINT fk_data_sources_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_dataset_raw (
                id INT UNSIGNED NOT NULL AUTO_INCREMENT,
                user_id INT NOT NULL,
                source_id INT NOT NULL,
                record_time DATETIME(6) NULL,
                ingested_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                content JSON NOT NULL,
                content_hash VARBINARY(32) NULL,
                content_type ENUM('json','csv','xml','text') NOT NULL DEFAULT 'json',
                schema_hint VARCHAR(128) NULL,
                status ENUM('ok','error','skipped') NOT NULL DEFAULT 'ok',
                error_message TEXT NULL,
                created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                PRIMARY KEY (id, ingested_at),
                KEY idx_user_source_time (user_id, source_id, record_time, id),
                KEY idx_ingested_at (ingested_at, id),
                UNIQUE KEY uq_user_source_hash (user_id, source_id, content_hash),
                CONSTRAINT fk_udr_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                CONSTRAINT fk_udr_source FOREIGN KEY (source_id) REFERENCES data_sources(id) ON DELETE CASCADE
            )
            ENGINE=InnoDB
            DEFAULT CHARSET=utf8mb4
            COLLATE=utf8mb4_unicode_ci;
        """)
        
        # Cleaned user_dataset_raw information. Analytics table that the frontend will query and display.
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS source_metrics_daily (
            `id` INT NOT NULL AUTO_INCREMENT,
            `user_id` INT NOT NULL,
            `day` DATE NOT NULL,
            `source_label` VARCHAR(64) NOT NULL,

            `leads` INT NOT NULL DEFAULT 0,
            `customers` INT NOT NULL DEFAULT 0,
            `orders` INT NOT NULL DEFAULT 0,

            `revenue_cents` BIGINT NOT NULL DEFAULT 0,
            `cost_cents` BIGINT NOT NULL DEFAULT 0,

            `churn_customers` INT NOT NULL DEFAULT 0,
            `total_customers` INT NOT NULL DEFAULT 0,

            `exits_total` INT NOT NULL DEFAULT 0,

            `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

            PRIMARY KEY (`id`),
            UNIQUE KEY `uq_smd_user_day_source` (`user_id`,`day`,`source_label`),
            KEY `ix_smd_user_source_day` (`user_id`,`source_label`,`day`),
            KEY `ix_smd_user_day` (`user_id`,`day`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
      
        """)
        # ETL Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS  `analytics_etl_state` (
            `id` INT NOT NULL AUTO_INCREMENT,
            `job` VARCHAR(64) NOT NULL UNIQUE,
            `last_raw_id` INT NOT NULL DEFAULT 0,
            `last_run_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (`id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_api_key (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NULL,
            api_key VARCHAR(255) NOT NULL,
            hashed_api_key VARCHAR(255) NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uq_user_api_key_api_key (api_key),
            UNIQUE KEY uq_user_api_key_hashed_api_key (hashed_api_key),
            CONSTRAINT fk_user_api_key_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """)

        # FAILED LOGIN ATTEMPT
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS failed_login_attempt (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ip_address VARCHAR(45) NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        );
        """)


        # Notification Center
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_notifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            display_location VARCHAR(255) NOT NULL UNIQUE,
            message TEXT NOT NULL,
            severity INT NOT NULL DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL 
                DEFAULT CURRENT_TIMESTAMP 
                ON UPDATE CURRENT_TIMESTAMP
        );
        """)

        # user_activity_log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                ip_address VARCHAR(45) NULL,
                user_id INT NULL,
                guest_id INT NULL,
                session_id VARCHAR(255) NULL,
                path TEXT NULL,
                method VARCHAR(10) NULL,
                status_code INT NULL,
                accessed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                query_params JSON NULL,
                referrer TEXT NULL,
                user_agent TEXT NULL,
                app_version VARCHAR(50) NULL,
                response_time FLOAT NULL,
                country VARCHAR(100) NULL,
                region VARCHAR(100) NULL,
                city VARCHAR(100) NULL,
                device_type VARCHAR(50) NULL,
                browser_name VARCHAR(50) NULL,
                os_name VARCHAR(50) NULL,
                event_message TEXT NULL,
                INDEX idx_activity_log_accessed_at (accessed_at),
                INDEX idx_activity_log_user_id (user_id),
                CONSTRAINT fk_activity_log_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );
        """)




        # These are the tables that the USER will upload their customer data to. They will use <uuid_hash>_<db_id_hash>_tablename for security. 
        # Indexing tables will need to be created to keep track of the user tables.
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_customers (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            email VARCHAR(255) UNIQUE,
            phone VARCHAR(50),
            address VARCHAR(255),
            city VARCHAR(255),
            state VARCHAR(255),
            country VARCHAR(255),
            zipcode VARCHAR(255),
            activity_status VARCHAR(255), 
            created_at DATE,
            referrer VARCHAR(255)
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS meta_leads (
            id BIGINT PRIMARY KEY,
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            email VARCHAR(255) UNIQUE,
            ad_id BIGINT,
            ad_name VARCHAR(255),
            adset_id BIGINT,
            adset_name VARCHAR(255),
            campaign_id BIGINT,
            campaign_name VARCHAR(255),
            form_id BIGINT,
            form_name VARCHAR(255),
            is_organic BOOLEAN,
            platform VARCHAR(50),
            retailer_item_id VARCHAR(255),
            lead_status VARCHAR(50),
            created_at DATE
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS wc_orders (
            id BIGINT PRIMARY KEY,
            parent_id BIGINT,
            status VARCHAR(50),
            currency VARCHAR(10),
            version VARCHAR(10),
            prices_include_tax BOOLEAN,
            date_created DATETIME,
            date_modified DATETIME,
            discount_total DECIMAL(10, 2),
            discount_tax DECIMAL(10, 2),
            shipping_total DECIMAL(10, 2),
            shipping_tax DECIMAL(10, 2),
            cart_tax DECIMAL(10, 2),
            total DECIMAL(10, 2),
            total_tax DECIMAL(10, 2),
            customer_id BIGINT,
            order_key VARCHAR(50),
            billing TEXT,
            shipping TEXT,
            payment_method VARCHAR(100),
            payment_method_title VARCHAR(100),
            transaction_id VARCHAR(100),
            customer_ip_address VARCHAR(45),
            customer_user_agent TEXT,
            created_via VARCHAR(50),
            customer_note TEXT,
            date_completed DATETIME,
            date_paid DATETIME,
            cart_hash VARCHAR(100),
            number VARCHAR(20),
            meta_data TEXT,
            line_items TEXT,
            tax_lines TEXT,
            shipping_lines TEXT,
            fee_lines TEXT,
            coupon_lines TEXT,
            refunds TEXT,
            payment_url TEXT,
            is_editable BOOLEAN,
            needs_payment BOOLEAN,
            needs_processing BOOLEAN,
            date_created_gmt DATETIME,
            date_modified_gmt DATETIME,
            date_completed_gmt DATETIME,
            date_paid_gmt DATETIME,
            store_credit_used DECIMAL(10, 2),
            currency_symbol VARCHAR(5)
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS customer_analysis (
            master_id BIGINT PRIMARY KEY AUTO_INCREMENT,
            wc_cx_id BIGINT UNIQUE, 
            ck_cx_id BIGINT UNIQUE,
            source VARCHAR(255),  
            ad_name VARCHAR(255),  
            first_name VARCHAR(255),
            last_name VARCHAR(255), 
            email VARCHAR(255) UNIQUE,
            created_at DATE,
            unsubscribed_on DATE,
            cx_tenure VARCHAR(30),
            activity_status VARCHAR(255),
            order_total DECIMAL(10, 2),
            subscription_total DECIMAL(10, 2),
            order_status VARCHAR(255),
            subscription_status VARCHAR(255),
            total_spend DECIMAL(10, 2),
            created_at_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cx_stats (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            customer_id BIGINT,
            email VARCHAR(255) UNIQUE,
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            origin VARCHAR(255),
            activity_status VARCHAR(255),
            created_at DATE,
            unsubscribed_on DATE,
            cx_tenure VARCHAR(30),
            subscribed_days INT,
            lifetime_value DECIMAL(10, 2),
            purchased_items TEXT,
            city VARCHAR(255),
            state VARCHAR(255),
            country VARCHAR(255),
            phone VARCHAR(50)
        );
        """)


        
        print("Database and tables ensured.")

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

