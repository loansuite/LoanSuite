import sqlite3
from flask import Flask, jsonify, request, g, send_file, send_from_directory
from datetime import datetime
import os
import threading

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

app = Flask(__name__)
DATABASE = 'loans.db'

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
    init_db()

# ------------------------------
# SENDGRID ASYNC EMAIL SENDER
# ------------------------------

def send_email_async(name, email, mobile, address):
    try:
        message = Mail(
            from_email='loansuite@gmail.com',
            to_emails='maxcandy4517@gmail.com',
            subject=f'🚨 NEW LOANSUITE DEMO REQUEST FROM {name}',
            html_content=f"""
            <h2>New Demo Request Received</h2>
            <p><strong>Name:</strong> {name}</p>
            <p><strong>Email:</strong> {email}</p>
            <p><strong>Mobile:</strong> {mobile}</p>
            <p><strong>Address:</strong> {address}</p>
            <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            """
        )

        sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
        sg.send(message)
        print("SendGrid Email Sent Successfully!")

    except Exception as e:
        print("SendGrid Error:", e)

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

    name = data['name']
    address = data.get('address', 'N/A')
    mobile = data.get('mobile', 'N/A')
    email = data['email']

    # Save to DB
    try:
        db = get_db()
        db.execute(
            "INSERT INTO demo_requests (name, address, mobile, email, timestamp) VALUES (?, ?, ?, ?, ?)",
            (name, address, mobile, email, datetime.now().isoformat())
        )
        db.commit()
    except Exception as e:
        print("DB ERROR:", e)
        return jsonify({'message': f'Database error: {e}'}), 500

    # Send email async
    threading.Thread(target=send_email_async, args=(name, email, mobile, address)).start()

    return jsonify({'message': 'Request saved. Email sent using SendGrid!'}), 201


# Google site verification
@app.route('/google1fda9bbe18536e5d.html')
def google_verify():
    return send_from_directory('.', 'google1fda9bbe18536e5d.html')

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
