from flask import Flask, jsonify, request, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = "CHANGE_ME_SECRET"
CORS(app, supports_credentials=True)

# ---- DB Setup ----
def init_db():
    with sqlite3.connect("users.db") as con:
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)
        con.commit()
init_db()

def get_user(username):
    with sqlite3.connect("users.db") as con:
        cur = con.cursor()
        cur.execute("SELECT id, username, password_hash FROM users WHERE username=?", (username,))
        return cur.fetchone()

# ---- Auth Routes ----
@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    u, p = data.get("username"), data.get("password")
    if not u or not p: return jsonify({"error":"Username and password required"}),400
    if get_user(u): return jsonify({"error":"Username exists"}),400
    with sqlite3.connect("users.db") as con:
        con.execute("INSERT INTO users (username, password_hash) VALUES (?,?)",
                    (u, generate_password_hash(p)))
    return jsonify({"message":"Registered"})

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    u, p = data.get("username"), data.get("password")
    user = get_user(u)
    if user and check_password_hash(user[2], p):
        session["user_id"], session["username"] = user[0], user[1]
        return jsonify({"username": user[1]})
    return jsonify({"error":"Invalid credentials"}),401

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message":"Logged out"})

@app.route("/api/current_user")
def current_user():
    return jsonify({"username": session.get("username")})

# ---- Your existing data endpoints ----
def require_login():
    return "user_id" in session

@app.route("/api/patient")
def get_patient():
    if not require_login(): return jsonify({"error":"Unauthorized"}),401
    return jsonify({
        "doctor_name": session["username"],
        "patient_name": "John Doe",
        "patient_age": 45,
        "patient_id": "123456",
        "vitals": {"bp": "120/80", "hr": "75 bpm", "temp": "98.6°F", "rr": 18},
        "notes": "Patient reports mild chest pain. ECG ordered. Continue current medications."
    })

@app.route("/api/appointments")
def get_appointments():
    if not require_login(): return jsonify({"error":"Unauthorized"}),401
    return jsonify({
        "appointments": [
            {"date":"2025-10-02","time":"09:00 AM","reason":"Follow-up Check"},
            {"date":"2025-10-10","time":"02:30 PM","reason":"Blood Work Review"},
        ]
    })

@app.route("/api/prescriptions")
def get_prescriptions():
    if not require_login(): return jsonify({"error":"Unauthorized"}),401
    return jsonify({
        "prescriptions":[
            {"drug":"Atenolol","dosage":"50 mg","frequency":"Once daily"},
            {"drug":"Lisinopril","dosage":"20 mg","frequency":"Once daily"},
        ]
    })

@app.route("/api/labs")
def get_labs():
    if not require_login(): return jsonify({"error":"Unauthorized"}),401
    return jsonify({
        "labs":[
            {"test":"Blood Panel","date":"2025-09-20","result":"Normal"},
            {"test":"ECG","date":"2025-09-25","result":"Pending"},
        ]
    })

if __name__ == "__main__":
    app.run(debug=True)
