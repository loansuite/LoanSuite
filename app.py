import sqlite3
from flask import Flask, jsonify, request, g, send_file, send_from_directory
from datetime import datetime
import os
import threading
import requests
from flask_cors import CORS

app = Flask(__name__)

# Enable full CORS for Render + custom domain
CORS(app, resources={r"/*": {"origins": "*"}})

DATABASE = 'loans.db'

# Load Brevo API Key from Render Environment
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "").strip()

RECEIVING_EMAILS = [
    "maxcandy4517@gmail.com",
    "loansuite@gmail.com"
]

# ------------------------------
# CORS RESPONSE FIX (IMPORTANT)
# ------------------------------
@app.after_request
def add_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    return response

# ------------------------------
# DATABASE FUNCTIONS
# ------------------------------
def get_db():
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

@app.before_request
def ensure_db():
    try:
        init_db()
    except Exception as e:
        print("DB INIT ERROR:", e)

# ------------------------------
# SEND EMAIL USING BREVO API
# ------------------------------
def send_async_email(name, email, mobile, address):
    if not BREVO_API_KEY:
        print("ERROR: BREVO_API_KEY missing!")
        return

    url = "https://api.brevo.com/v3/smtp/email"

    payload = {
        "sender": {
            "name": "LoanSuite",
            "email": "loansuite@gmail.com"
        },
        "to": [{"email": r} for r in RECEIVING_EMAILS],
        "subject": f"🚨 NEW LOANSUITE DEMO REQUEST from {name}",
        "textContent": f"""
New demo request received:

Name: {name}
Email: {email}
Mobile: {mobile}
Address: {address}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    }

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }

    try:
        res = requests.post(url, json=payload, headers=headers)
        print("Brevo API Response:", res.text)
    except Exception as e:
        print("Email sending failed:", e)

# ------------------------------
# ROUTES
# ------------------------------
@app.route('/')
def index():
    return send_file('index.html')


@app.route('/api/demo_requests', methods=['POST'])
def create_demo_request():
    data = request.get_json()

    if not data or "name" not in data or "email" not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    name = data.get("name")
    address = data.get("address", "N/A")
    mobile = data.get("mobile", "N/A")
    email = data.get("email")

    # Save into DB
    try:
        db = get_db()
        db.execute(
            "INSERT INTO demo_requests (name, address, mobile, email, timestamp) VALUES (?, ?, ?, ?, ?)",
            (name, address, mobile, email, datetime.now().isoformat())
        )
        db.commit()
    except Exception as e:
        print("DB ERROR:", e)
        return jsonify({'message': 'Database error'}), 500

    # Send email in background
    threading.Thread(
        target=send_async_email,
        args=(name, email, mobile, address)
    ).start()

    return jsonify({'message': 'Request saved & email sent!'}), 201

# Google verification
@app.route('/google1fda9bbe18536e5d.html')
def google_verify():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)),
                               'google1fda9bbe18536e5d.html')

# TEMPORARY, DESTRUCTIVE CLEANUP ROUTE (DELETE THIS AFTER USE!)
@app.route('/CLEANUP-SITEMAP-NOW')
def delete_old_sitemap():
    # Attempt to find and delete the lingering corrupted file artifact from the server
    old_sitemap_path = os.path.join(app.root_path, 'sitemap.xml')
    if os.path.exists(old_sitemap_path):
        try:
            os.remove(old_sitemap_path)
            # File is deleted. We expect the next request to sitemap.xml to be a 404.
            return "SUCCESS: Old sitemap.xml artifact deleted. **IMMEDIATELY REMOVE THIS ROUTE FROM app.py AND REDEPLOY!**", 200
        except Exception as e:
            # This often happens if permissions are restricted on the free tier
            return f"ERROR: Failed to delete sitemap.xml. Check logs for permission error. Error: {e}", 500
    else:
        # File artifact is already gone.
        return "INFO: Old sitemap.xml not found on server. Proceed to check sitemap URLs.", 200

# Sitemap - This route ONLY handles the NEW, correct file path
@app.route('/sitemap-loansuite.xml')
def sitemap():
    # This must serve the file named 'sitemap-loansuite.xml'
    return send_from_directory('.', 'sitemap-loansuite.xml')
    
# ------------------------------
# RUN SERVER
# ------------------------------
if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)



