#Backend to dr view frontEnd.html and login.html

from flask import Flask, jsonify, request, session, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__, static_folder="static")
app.secret_key = "CHANGE_ME_SECRET"
CORS(app, supports_credentials=True)

# ---- MongoDB Connection ----
MONGO_URI = "mongodb://localhost:27017"  # or your Atlas connection string
client = MongoClient(MONGO_URI)
db = client["MiniEMR"]
users_col = db["users"]

# ---- Serve Frontend ----
@app.route("/")
def serve_login():
    return send_from_directory("static", "login.html")

@app.route("/FrontEnd.html")
def serve_frontend():
    return send_from_directory("static", "FrontEnd.html")

@app.route("/<path:path>")
def serve_static_files(path):
    return send_from_directory("static", path)

# ---- User Helpers ----
def get_user(username):
    return users_col.find_one({"username": username})

# ---- Auth Routes ----
@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    u, p = data.get("username"), data.get("password")

    if not u or not p:
        return jsonify({"error": "Username and password required"}), 400

    if get_user(u):
        return jsonify({"error": "Username already exists"}), 400

    users_col.insert_one({
        "username": u,
        "password_hash": generate_password_hash(p)
    })

    return jsonify({"message": "User registered successfully"})

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    u, p = data.get("username"), data.get("password")
    user = get_user(u)

    if user and check_password_hash(user["password_hash"], p):
        session["user_id"] = str(user["_id"])
        session["username"] = user["username"]
        return jsonify({"username": user["username"]})
    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})

@app.route("/api/current_user")
def current_user():
    return jsonify({"username": session.get("username")})

# ---- Data Endpoints ----
def require_login():
    return "user_id" in session

@app.route("/api/patient")
def get_patient():
    if not require_login():
        return jsonify({"error": "Unauthorized"}), 401
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
    if not require_login():
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({
        "appointments": [
            {"date": "2025-10-02", "time": "09:00 AM", "reason": "Follow-up Check"},
            {"date": "2025-10-10", "time": "02:30 PM", "reason": "Blood Work Review"},
        ]
    })

@app.route("/api/prescriptions")
def get_prescriptions():
    if not require_login():
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({
        "prescriptions": [
            {"drug": "Atenolol", "dosage": "50 mg", "frequency": "Once daily"},
            {"drug": "Lisinopril", "dosage": "20 mg", "frequency": "Once daily"},
        ]
    })

@app.route("/api/labs")
def get_labs():
    if not require_login():
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({
        "labs": [
            {"test": "Blood Panel", "date": "2025-09-20", "result": "Normal"},
            {"test": "ECG", "date": "2025-09-25", "result": "Pending"},
        ]
    })

if __name__ == "__main__":
    app.run(debug=True)
