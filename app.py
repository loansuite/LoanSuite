import sqlite3
from flask import Flask, jsonify, request, g, send_file, send_from_directory
from flask_mail import Mail, Message
from datetime import datetime
import os

app = Flask(__name__)
DATABASE = 'loans.db'

# --- EMAIL CONFIGURATION ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'loansuite@gmail.com'
app.config['MAIL_PASSWORD'] = 'wbwp egdh sjzw vllb'
app.config['MAIL_DEFAULT_SENDER'] = 'loansuite@gmail.com'

RECEIVING_EMAIL = 'maxcandy4517@gmail.com'
mail = Mail(app)

# ------------------------------
# DATABASE FUNCTIONS
# ------------------------------

def get_db():
    """Return SQLite DB connection"""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Create table if missing"""
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS demo_requests (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            mobile TEXT,
            email TEXT NOT NULL,
            timestamp TEXT NOT NULL
        );
    """)
    db.commit()

# Auto-create table before every request (Fix for Gunicorn/Render)
@app.before_request
def ensure_db():
    try:
        init_db()
    except Exception as e:
        print("DB INIT ERROR:", e)

# ------------------------------
# ROUTES
# ------------------------------

@app.route('/')
def index():
    try:
        return send_file('index.html')
    except Exception as e:
        return f"Error loading site: {e}", 500


@app.route('/api/demo_requests', methods=['POST'])
def create_demo_request():
    data = request.get_json()

    if not data or "name" not in data or "email" not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    name = data.get('name')
    address = data.get('address', 'N/A')
    mobile = data.get('mobile', 'N/A')
    email = data.get('email')

    # --- Save to Database ---
    try:
        db = get_db()
        db.execute(
            "INSERT INTO demo_requests (name, address, mobile, email, timestamp) VALUES (?, ?, ?, ?, ?)",
            (name, address, mobile, email, datetime.now().isoformat())
        )
        db.commit()
    except Exception as e:
        print("DB ERROR:", e)

    # --- Send Email Safely ---
    email_status = ""
    try:
        msg = Message(
            subject=f"🚨 NEW LOANSUITE DEMO REQUEST from {name}",
            recipients=[RECEIVING_EMAIL]
        )
        msg.body = f"""
A new demo request was submitted:

Name: {name}
Email: {email}
Mobile: {mobile}
Address: {address}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        mail.send(msg)
        email_status = "Email sent successfully!"
    except Exception as e:
        print("EMAIL ERROR:", e)
        email_status = "Email failed, but request saved."

    return jsonify({'message': f'Request saved. {email_status}'}), 201


# Google verification
@app.route('/google1fda9bbe18536e5d.html')
def google_verify():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)),
                               'google1fda9bbe18536e5d.html')


# Sitemap
@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('.', 'sitemap.xml')


# ------------------------------
# LOCAL DEVELOPMENT ONLY
# ------------------------------
if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)
