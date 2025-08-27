## Synevyr Local Setup (macOS)

### Prerequisites

1. **Install Homebrew** (if not installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install MySQL**:
   ```bash
   brew install mysql
   brew services start mysql
   ```

3. **Set root password for MySQL**:
   ```bash
   mysql_secure_installation
   ```
   Use this when prompted:
   ```
   root password: Synevyr_SQL_PWD
   ```
   
4. **Install Redis**:
   ```bash
   brew install redis
   brew services start redis
   ```
---

### Project Setup

1. **Clone the repository** (if you haven't):
   ```bash
   git clone https://github.com/Carpathian-LLC/Synevyr.git
   cd synevyr
   ```

   **CD into the frontend and install NPM**
   ```bash
   cd /Users/YOUR_USERNAME/Development/synevyr/frontend
   npm install
   ```

2. **Run the setup + seed script**:
   ```bash
   cd /Users/YOUR_USERNAME/Development/synevyr
   python3 run_me_first.py
   ```

   This will:
   - Create a `.venv` (if missing)
   - Install all dependencies from `requirements.txt`
   - Auto-generate a `keys.env` with secure random session/webhook keys
   - Seed synthetic customer and order data into your local MySQL instance
   - Start the Flask backend server on port `2001`
   - Start the React frontend on port `2000`

---

### Server Startup Message

Once complete, you’ll see:

```
✅ Data seeded successfully.
🧪 Starting Flask server...

 * Running on http://localhost:2001 (Press CTRL+C to quit)
```

Open your browser to [http://localhost:2001](http://localhost:2001) to access the backend.

Open your browser to [http://localhost:2000](http://localhost:2000) to access the frontend.

---

### 🔁 To re-run later:

```bash
cd /Users/YOUR_USERNAME/synevyr/
python3 autostart.py
```
This will start all the required services easily!