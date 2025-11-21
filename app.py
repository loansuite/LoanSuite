import sqlite3
from flask import Flask, jsonify, request, g, send_file
from flask_mail import Mail, Message
from datetime import datetime

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

# --- Database Setup Functions ---

def get_db():
    """Establishes a connection to the database."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row 
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Initializes the database schema (UPDATED: added address and mobile)."""
    with app.app_context():
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

# --- Website Route ---
@app.route('/')
def index():
    """Serves the main index.html file to the browser."""
    try:
        return send_file('index.html')
    except Exception as e:
        return f"<h1>Error serving index.html: {e}</h1>", 500

# --- API Route for Lead Capture (FINAL VERSION) ---

@app.route('/api/demo_requests', methods=['POST'])
def create_demo_request():
    """API endpoint to record a demo request AND send an email alert."""
    data = request.get_json()
    
    required_fields = ("name", "email")
    if not all(k in data for k in required_fields):
        # Note: Address and Mobile are now treated as optional for validation, 
        # but required for insertion (handled by data.get defaults).
        return jsonify({'error': 'Missing required fields: name or email'}), 400
    
    # Retrieve all four fields
    name = data.get('name')
    address = data.get('address', 'N/A') 
    mobile = data.get('mobile', 'N/A')   
    email = data.get('email')
    
    # 1. Database Logging Attempt
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO demo_requests (name, address, mobile, email, timestamp) VALUES (?, ?, ?, ?, ?)",
            (name, address, mobile, email, datetime.now().isoformat())
        )
        db.commit()
    except Exception as e:
        print(f"DATABASE ERROR: Failed to record demo request: {e}")

    # 2. Email Notification Attempt
    try:
        msg = Message(
            subject=f"🚨 NEW LOANSUITE DEMO REQUEST from {name}",
            recipients=[RECEIVING_EMAIL]
        )
        # Email body includes all four details
        msg.body = f"""
        A new demo request has been submitted through your LoanSuite website.

        --- Lead Details ---
        Name: {name}
        Email: {email}
        Mobile: {mobile}
        Address/Location: {address}
        Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        ---
        Please contact the lead immediately.
        """
        mail.send(msg)
        
        return jsonify({'message': 'Demo request successfully recorded and email sent to LoanSuite team!'}), 201

    except Exception as e:
        print(f"EMAIL SENDING FAILED: {e}")
        return jsonify({'message': 'Demo request accepted, but notification email failed to send (check server logs).'}), 201

from flask import send_from_directory

@app.route('/google1fda9bbe18536e5d.html')
def google_verify():
    return send_from_directory('.', 'google1fda9bbe18536e5d.html')

# --- Server Start ---

if __name__ == '__main__':
    with app.app_context():
        init_db()
    
    app.run(debug=True)

