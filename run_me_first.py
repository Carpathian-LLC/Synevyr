# ------------------------------------------------------------------------------------
# Synevyr local bootstrap: venv + seed + launch backend and frontend in separate terminals
# ------------------------------------------------------------------------------------
# Imports
import os
import sys
import subprocess
from pathlib import Path
import shlex
import secrets
import platform
from pathlib import Path
import traceback
from importlib.machinery import SourceFileLoader

# ------------------------------------------------------------------------------------
# Vars:

ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / ".synevyr_venv"
REQUIREMENTS = ROOT / "requirements.txt"
ENV_FILE = ROOT / "keys.env"
PYTHON_BIN = VENV_DIR / "bin" / "python"

BACKEND_DIR = ROOT / "backend"
BACKEND_ENTRY = BACKEND_DIR / "run.py"

FRONTEND_DIR = ROOT / "frontend"
FRONTEND_PORT = os.environ.get("SYNEVYR_FRONTEND_PORT", "2000")  # override with env if needed

FRONTEND_ENV_LOCAL = FRONTEND_DIR / ".env.local"
FRONTEND_ENV_PROD = FRONTEND_DIR / ".env.production"

AUTOSTART_PATH = ROOT / "autostart.py"

def _load_autostart():
    if not AUTOSTART_PATH.exists():
        print(f"autostart.py not found at {AUTOSTART_PATH}")
        sys.exit(1)
    # Load as a module regardless of PYTHONPATH
    return SourceFileLoader("synevyr_autostart", str(AUTOSTART_PATH)).load_module()

# ------------------------------------------------------------------------------------
# Helpers:
def load_env_keys():
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / "keys.env"
    if not env_path.exists():
        print(f"❌ keys.env not found at {env_path}")
        sys.exit(1)

    load_dotenv(dotenv_path=env_path)
    print(f"[DEBUG] keys.env loaded from: {env_path}")

def create_venv():
    print("Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)

def install_dependencies():
    if not REQUIREMENTS.exists():
        print("requirements.txt not found. Skipping pip install.")
        return
    print("Installing dependencies...")
    subprocess.run([str(PYTHON_BIN), "-m", "pip", "install", "-r", str(REQUIREMENTS)], check=True)

def generate_keys_env():
    if ENV_FILE.exists():
        print("keys.env already exists. Skipping generation.")
        return

    print("Generating keys.env...")
    session_key = secrets.token_hex(128)
    webhook_key = secrets.token_hex(32)

    contents = f"""# Dev Synevyr keys.env

FLASK_ENV=development
DOMAIN="http://localhost:{FRONTEND_PORT}"

DB_MODE=local
DATABASE=db_synevyr

# Flask secret keys for sessions/webhooks
FLASK_SESSION_KEY={session_key}
FLASK_WEBHOOK_KEY={webhook_key}

# Frontend:
NEXT_PUBLIC_GA_ID= ADD_YOUR_GOOGLE_ANALYTICS_KEY_HERE


# LOCAL DATABASE CONFIG
DEV_DB_HOST=127.0.0.1
DEV_DB_USER=root
DEV_DB_PASSWORD=Synevyr_SQL_PWD
DEV_DB_PORT=3306
""".strip() + "\n"

    ENV_FILE.write_text(contents, encoding="utf-8")
    print("keys.env created.")

def generate_frontend_envs(overwrite: bool = False):
    """
    Create frontend/.env.local and frontend/.env.production
    Contents:
        NEXT_PUBLIC_API_BASE_URL=http://localhost:2001
        NEXT_PUBLIC_SOCKET_URL=http://localhost:2001
    Set SYNEVYR_OVERWRITE_FRONTEND_ENVS=1 to force overwrite.
    """
    if not FRONTEND_DIR.exists():
        print(f"❌ Frontend directory not found at {FRONTEND_DIR}")
        sys.exit(1)

    env_contents = (
        "NEXT_PUBLIC_API_BASE_URL=http://localhost:2001\n"
        "NEXT_PUBLIC_SOCKET_URL=http://localhost:2001\n"
    )

    def write_env(path: Path):
        if path.exists() and not overwrite:
            print(f"{path.name} already exists. Skipping generation.")
            return
        path.write_text(env_contents, encoding="utf-8")
        print(f"{path.name} created.")

    print("Generating frontend env files...")
    write_env(FRONTEND_ENV_LOCAL)
    write_env(FRONTEND_ENV_PROD)

def seed_database():
    """
    Run your seeding logic exactly once (inside the venv).
    No subprocess, no re-invocation of this script.
    """
    print("[DEBUG] Starting database seed...")
    # If your project seeds via generators/generator.py, call it directly:
    try:
        from generators import generator
    except Exception as e:
        print("❌ Could not import seeding module (generators/generator.py).")
        print("   Make sure the file exists and is importable from project root.")
        print(f"   Import error: {e}")
        sys.exit(1)

    try:
        generator.main()
        print("✅ Database seeding complete.")
    except Exception as e:
        print("❌ Seeding failed inside generator.main().")
        print(f"   Error: {e}")
        raise

def mac_escape(s: str) -> str:
    # Escape for AppleScript string literal
    return s.replace("\\", "\\\\").replace('"', '\\"')

def open_terminal_window_mac(command: str):
    """
    Open a new macOS Terminal window and run the given command.
    Uses default login shell initialization so nvm/nodeenv users still get their profile.
    """
    cmd_escaped = mac_escape(command)
    osa = f'''
tell application "Terminal"
    activate
    do script "{cmd_escaped}"
end tell
'''
    subprocess.run(["osascript", "-e", osa], check=True)

def start_backend_in_new_terminal_mac():
    # Activate venv, export env, run Flask backend
    lines = [
        f'cd {shlex.quote(str(BACKEND_DIR))}',
        f'source {shlex.quote(str(VENV_DIR / "bin" / "activate"))}',
        f'set -a; source {shlex.quote(str(ENV_FILE))}; set +a',
        f'{shlex.quote(str(PYTHON_BIN))} {shlex.quote(str(BACKEND_ENTRY))}'
    ]
    open_terminal_window_mac(" && ".join(lines))

def start_frontend_in_new_terminal_mac():
    # Run Next.js with PORT=2000
    lines = [
        f'cd {shlex.quote(str(FRONTEND_DIR))}',
        f'export PORT={shlex.quote(FRONTEND_PORT)}',
        # If you use pnpm or yarn, replace the next line accordingly
        'npm run dev'
    ]
    open_terminal_window_mac(" && ".join(lines))

def create_database_and_tables():
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import OperationalError
    host = os.getenv("DEV_DB_HOST", "127.0.0.1")
    user = os.getenv("DEV_DB_USER", "root")
    password = os.getenv("DEV_DB_PASSWORD", "")
    port = os.getenv("DEV_DB_PORT", "3306")
    db_name = os.getenv("DATABASE", "db_synevyr")

    print("[DEBUG] Loaded DB credentials from environment/keys.env:")
    print(f"       DEV_DB_HOST = {host}")
    print(f"       DEV_DB_USER = {user}")
    print(f"       DEV_DB_PASSWORD = {password}")
    print(f"       DEV_DB_PORT = {port}")
    print(f"       DATABASE = {db_name}")

    print(f"[DEBUG] Connecting to MySQL at {host}:{port} as {user}")
    print(f"[DEBUG] Target database: {db_name}")

    try:
        # Step 1: Always connect to a safe system DB first
        sys_engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}/mysql")
        with sys_engine.begin() as conn:
            print("[DEBUG] Connected to 'mysql' system database.")

            # Step 2: Check if target DB exists
            result = conn.execute(
                text("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = :dbname"),
                {"dbname": db_name}
            ).fetchone()

            if not result:
                print(f"Database '{db_name}' does not exist. Creating it now...")
                conn.execute(text(f"CREATE DATABASE `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"))
            else:
                print(f"Database '{db_name}' already exists.")
    except OperationalError as e:
        print("❌ Database connection failed.")
        print("Likely causes:")
        print("  • MySQL server is not running")
        print("  • Incorrect username/password in keys.env")
        print("  • Host/port is wrong")
        print("-"*80)
        #print(f"Error: {e.orig}")  # Underlying PyMySQL message
        sys.exit(1)

    try:
        # Step 2: Connect to the target DB
        print(f"[DEBUG] Connecting to target DB `{db_name}`...")
        db_engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}")
        with db_engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        print(f"✅ Successfully connected to `{db_name}`.")
    except OperationalError as e:
        print("❌ Database connection failed.")
        print("Likely causes:")
        print("  • MySQL server is not running")
        print("  • Incorrect username/password in keys.env")
        print("  • Host/port is wrong")
        print("-"*80)
        #print(f"Error: {e.orig}")  # Underlying PyMySQL message
        sys.exit(1)

    try:
        # Step 3: Create tables
        print("[DEBUG] Creating tables if they do not exist...")
        with db_engine.begin() as conn:
            conn.execute(text("""
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
            """))

            conn.execute(text("""
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
            """))

            conn.execute(text("""
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
            """))

            conn.execute(text("""
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
            """))

            conn.execute(text("""
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
            """))
        print("✅ Tables created or already exist.")
    except OperationalError as e:
        print("❌ Database connection failed.")
        print("Likely causes:")
        print("  • MySQL server is not running")
        print("  • Incorrect username/password in keys.env")
        print("  • Host/port is wrong")
        print("-"*80)
        #print(f"Error: {e.orig}")  # Underlying PyMySQL message
        sys.exit(1)

def main():
    if not VENV_DIR.exists():
        create_venv()
        install_dependencies()
    else:
        pass

    generate_keys_env()

    try:
        create_database_and_tables()
    except subprocess.CalledProcessError as e:
        print("\n" + "="*80)
        print("❌ ERROR: Seeding process failed.")
        print("This usually means:")
        print("  • MySQL server is not running")
        print("  • Incorrect database credentials in keys.env")
        print("  • Required Python packages (e.g. mysql-connector-python, etc.) are missing")
        print("  • The 'db_synevyr' database could not be created or accessed")
        print("-"*80)
        print(f"Full error details:\n{e}")
        print("="*80 + "\n")
        sys.exit(1)


    # After seeding, open two Terminal windows and start backend and frontend
    if platform.system() == "Darwin":
        print("Launching backend in a new Terminal window...")
        start_backend_in_new_terminal_mac()
        print("Launching frontend in a new Terminal window on port", FRONTEND_PORT, "...")
        start_frontend_in_new_terminal_mac()
        print("Done. Backend and frontend are running in separate Terminal windows.")
    else:
        print("Non-macOS OS detected. Cannot open separate Terminal windows automatically.")
        print("Manual commands:")
        print(f"1) Backend:\n   cd {BACKEND_DIR}\n   source {VENV_DIR}/bin/activate\n   export $(grep -v '^#' {ENV_FILE} | xargs)\n   {PYTHON_BIN} {BACKEND_ENTRY}")
        print(f"2) Frontend:\n   cd {FRONTEND_DIR}\n   export PORT={FRONTEND_PORT}\n   npm run dev")

# ------------------------------------------------------------------------------------
# Bootstrap runner

CHECKLIST_FILE = ROOT / "bootstrap_checklist.txt"

def mark_step(step, status="OK", error=None):
    """Append the step status to the checklist file."""
    with open(CHECKLIST_FILE, "a", encoding="utf-8") as f:
        if status == "OK":
            f.write(f"{step}: SUCCESS\n")
        else:
            f.write(f"{step}: FAILED - {error}\n")

def step_done(step):
    """Check if a step is already marked as SUCCESS."""
    if not CHECKLIST_FILE.exists():
        return False
    with open(CHECKLIST_FILE, "r", encoding="utf-8") as f:
        return any(line.startswith(f"{step}: SUCCESS") for line in f)

def run_bootstrap():
    # Steps that run in system Python (OUTSIDE VENV)
    system_steps = [
        ("venv_created", create_venv),
        ("dependencies_installed", install_dependencies),
        ("keys_env_generated", generate_keys_env),
        ("frontend_envs_generated",
         lambda: generate_frontend_envs(
             overwrite=os.getenv("SYNEVYR_OVERWRITE_FRONTEND_ENVS") == "1"
         )),
    ]

    for step_name, func in system_steps:
        if step_done(step_name):
            print(f"✔ {step_name} already completed. Skipping.")
            continue
        print(f"▶ Running step: {step_name}")
        try:
            func()
            mark_step(step_name, "OK")
        except Exception as e:
            print(f"❌ Step '{step_name}' failed: {e}")
            mark_step(step_name, "FAIL", str(e))
            sys.exit(1)

    # Relaunch inside venv for the rest
    if sys.prefix != str(VENV_DIR):
        print("🔄 Re-running inside virtual environment for DB + seed steps...")
        subprocess.run([str(PYTHON_BIN), __file__], check=True)
        sys.exit(0)

    # Steps that require venv
    def db_and_tables_created_step():
        load_env_keys()
        create_database_and_tables()

    def data_seeded_step():
        load_env_keys()
        seed_database()

    venv_steps = [
        ("db_and_tables_created", db_and_tables_created_step),
        ("data_seeded", data_seeded_step),
    ]


    for step_name, func in venv_steps:
        if step_done(step_name):
            print(f"✔ {step_name} already completed. Skipping.")
            continue
        print(f"▶ Running step: {step_name}")
        try:
            func()
            mark_step(step_name, "OK")
        except Exception as e:
            print(f"❌ Step '{step_name}' failed: {e}")
            mark_step(step_name, "FAIL", str(e))
            sys.exit(1)

# Run bootstrap process
# Run bootstrap process
if __name__ == "__main__":
    run_bootstrap()

    if platform.system() == "Darwin":
        auto = _load_autostart()

        # autostart.py already validates paths and opens new Terminal windows.
        print("Launching backend...")
        auto.start_backend()

        print(f"Launching frontend on port {FRONTEND_PORT}...")
        # autostart uses its own default port; export an override if needed.
        # If you want autostart to honor this script's port, set SYNEVYR_FRONTEND_PORT
        # and read it inside autostart, or adjust autostart to read from env.
        auto.start_frontend()

        print("Launching Celery worker...")
        auto.start_celery_worker()

        print("Launching Celery beat...")
        auto.start_celery_beat()

        print("Done. Services launched in separate Terminal windows.")
    else:
        print("Non-macOS OS detected. Cannot open separate Terminal windows automatically.")
        print("Manual commands:")
        print(f"1) Backend:\n   cd {BACKEND_DIR}\n   source {VENV_DIR}/bin/activate\n   export $(grep -v '^#' {ENV_FILE} | xargs)\n   {PYTHON_BIN} {BACKEND_ENTRY}")
        print(f"2) Frontend:\n   cd {FRONTEND_DIR}\n   export PORT={FRONTEND_PORT}\n   npm run dev")
        print("3) Celery worker:\n   cd backend\n   source ../.synevyr_venv/bin/activate\n   celery -A celery_app.celery worker --loglevel=INFO -E")
        print("4) Celery beat:\n   cd backend\n   source ../.synevyr_venv/bin/activate\n   celery -A celery_app.celery beat --loglevel=INFO")
