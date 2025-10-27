import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# -------------------- Load Environment Variables --------------------
# Loads .env file variables for sensitive data like SECRET_KEY and MongoDB URI
load_dotenv()

# -------------------- Initialize Flask App --------------------
app = Flask(__name__)
# Secret key used for session management. Fallback provided in case .env is missing
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret_key")

# -------------------- Connect to MongoDB --------------------
mongo_uri = os.getenv("MONGO_URI")  # URI stored in .env
client = MongoClient(mongo_uri)
db = client["Mini_Emr_db"]          # Database name
patients = db["Patients"]            # Collection for patients
doctors = db["Doctors"]              # Collection for doctors

# -------------------- Home Route --------------------
@app.route("/")
def home():
    """
    Renders the home page (index.html)
    """
    return render_template("index.html")


# -------------------- Patient Registration --------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Handles patient registration.
    GET: Shows the registration form.
    POST: Validates input, hashes password, saves patient in MongoDB.
    """
    if request.method == "POST":
        # Retrieve form data
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        opid = request.form.get("opid")
        password = request.form.get("password")

        # Basic validation: all fields required
        if not first_name or not last_name or not opid or not password:
            return render_template("register.html", error="Please fill in all fields.")

        # Check if OPID (username) already exists
        existing_patient = patients.find_one({"OPID": opid})
        if existing_patient:
            return render_template("register.html", error="That OPID is already taken.")

        # Hash the password before storing it
        hashed_pw = generate_password_hash(password)

        # Create patient document
        new_patient = {
            "First Name": first_name,
            "Last Name": last_name,
            "OPID": opid,
            "Password": hashed_pw,
            "records": []  # Initialize empty medical records
        }

        # Insert new patient into MongoDB
        patients.insert_one(new_patient)

        # Redirect user to login page after successful registration
        return redirect(url_for("patient_login"))

    # Render registration form if GET request
    return render_template("register.html")


# -------------------- Patient Login --------------------
@app.route("/patientlogin", methods=["GET", "POST"])
def patient_login():
    """
    Handles patient login.
    GET: Shows login form.
    POST: Authenticates user and sets session if successful.
    """
    if request.method == "POST":
        opid = request.form.get("opid")
        password = request.form.get("password")

        # Ensure both username and password are provided
        if not opid or not password:
            return render_template("PatientLogin.html", error="Please Enter Username and Password")

        # Find patient by OPID
        patient = patients.find_one({"OPID": opid})
        if not patient:
            return render_template("PatientLogin.html", error="Invalid Username or Password")

        stored_hash = patient.get("Password")
        if not stored_hash:
            return render_template("PatientLogin.html", error="No Password Found")

        # Verify password
        if check_password_hash(stored_hash, password):
            # Set patient session to track logged-in state
            session["patient_id"] = str(patient["_id"])
            return redirect(url_for("patient_view", id=str(patient["_id"])))
        else:
            return render_template("PatientLogin.html", error="Invalid Username or Password")

    # Render login form if GET request
    return render_template("PatientLogin.html")


# -------------------- Patient View --------------------
@app.route("/patients/<id>")
def patient_view(id):
    """
    Displays patient dashboard.
    Only accessible if logged in as that patient.
    """
    if "patient_id" not in session or session["patient_id"] != id:
        return redirect(url_for("patient_login"))

    # Fetch patient data
    patient = patients.find_one({"_id": ObjectId(id)})
    if not patient:
        return "Patient not found", 404

    # Prepare data for template
    patient_data = {
        "first_name": patient.get("First Name", ""),
        "last_name": patient.get("Last Name", ""),
        "opid": patient.get("OPID", "")
    }

    return render_template("patientView.html", patient=patient_data)


# -------------------- Doctor Login --------------------
@app.route("/doctorlogin", methods=["GET", "POST"])
def doctor_login():
    """
    Handles doctor login.
    Similar to patient login.
    """
    if request.method == "POST":
        opid = request.form.get("opid")
        password = request.form.get("password")

        if not opid or not password:
            return render_template("DoctorLogin.html", error="Please Enter Username and Password")

        doctor = doctors.find_one({"OPID": opid})
        if not doctor:
            return render_template("DoctorLogin.html", error="Invalid Username or Password")

        stored_hash = doctor.get("Password")
        if not stored_hash:
            return render_template("DoctorLogin.html", error="No Password Found")

        if check_password_hash(stored_hash, password):
            session["doctor_id"] = str(doctor["_id"])
            return redirect(url_for("doctor_view", id=str(doctor["_id"])))
        else:
            return render_template("DoctorLogin.html", error="Invalid Username or Password")

    return render_template("DoctorLogin.html")


# -------------------- Doctor Dashboard --------------------
@app.route("/doctors/<id>")
def doctor_view(id):
    """
    Displays all patients to the logged-in doctor.
    """
    if "doctor_id" not in session or session["doctor_id"] != id:
        return redirect(url_for("doctor_login"))

    doctor = doctors.find_one({"_id": ObjectId(id)})
    if not doctor:
        return "Doctor not found", 404

    # Fetch all patients
    all_patients = list(patients.find())

    doctor_data = {
        "first_name": doctor.get("First Name", ""),
        "last_name": doctor.get("Last Name", ""),
        "opid": doctor.get("OPID", "")
    }

    return render_template("DoctorView.html", doctor=doctor_data, patients=all_patients)


# -------------------- Doctor Add Medical Record --------------------
@app.route("/add_record/<patient_id>", methods=["GET", "POST"])
def add_record(patient_id):
    """
    Allows doctor to add a new medical record for a patient.
    """
    if "doctor_id" not in session:
        return redirect(url_for("doctor_login"))

    patient = patients.find_one({"_id": ObjectId(patient_id)})
    if not patient:
        return "Patient not found", 404

    if request.method == "POST":
        new_record = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "blood_pressure": request.form.get("blood_pressure"),
            "temperature": request.form.get("temperature"),
            "notes": request.form.get("notes")
        }

        # Append record to patient's records array
        patients.update_one(
            {"_id": ObjectId(patient_id)},
            {"$push": {"records": new_record}}
        )

        return redirect(url_for("doctor_view", id=session["doctor_id"]))

    return render_template("add_record.html", patient=patient)


# -------------------- Patient View Records --------------------
@app.route("/view_records/<id>")
def view_records(id):
    """
    Allows a patient to view their own medical records.
    """
    if "patient_id" not in session or session["patient_id"] != id:
        return redirect(url_for("patient_login"))

    patient = patients.find_one({"_id": ObjectId(id)})
    if not patient:
        return "Patient not found", 404

    records = patient.get("records", [])
    return render_template("view_records.html", patient=patient, records=records)


# -------------------- Logout Routes --------------------
@app.route("/logout")
def logout():
    """
    Logs out patient by clearing session.
    """
    session.clear()
    return redirect(url_for("patient_login"))


@app.route("/doctorlogout")
def doctor_logout():
    """
    Logs out doctor by removing doctor_id from session.
    """
    session.pop("doctor_id", None)
    return redirect(url_for("doctor_login"))


# -------------------- Run Flask App --------------------
if __name__ == "__main__":
    app.run(debug=True)
import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import check_password_hash
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret_key")

# Connect MongoDB
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client["Mini_Emr_db"]
patients = db["Patients"]
doctors = db["Doctors"]

# -------------------- Home --------------------
@app.route("/")
def home():
    return render_template("index.html")

# -------------------- Patient Login --------------------
@app.route("/patientlogin", methods=["GET", "POST"])
def patient_login():
    if request.method == "POST":
        opid = request.form.get("opid")
        password = request.form.get("password")

        if not opid or not password:
            return render_template("PatientLogin.html", error="Please Enter Username and Password")

        patient = patients.find_one({"OPID": opid})
        if not patient:
            return render_template("PatientLogin.html", error="Invalid Username or Password")

        stored_hash = patient.get("Password")
        if not stored_hash:
            return render_template("PatientLogin.html", error="No Password Found")

        if check_password_hash(stored_hash, password):
            session["patient_id"] = str(patient["_id"])
            return redirect(url_for("patient_view", id=str(patient["_id"])))
        else:
            return render_template("PatientLogin.html", error="Invalid Username or Password")

    return render_template("PatientLogin.html")


# -------------------- Patient View --------------------
@app.route("/patients/<id>")
def patient_view(id):
    if "patient_id" not in session or session["patient_id"] != id:
        return redirect(url_for("patient_login"))

    patient = patients.find_one({"_id": ObjectId(id)})
    if not patient:
        return "Patient not found", 404

    patient_data = {
        "first_name": patient.get("First Name", ""),
        "last_name": patient.get("Last Name", ""),
        "opid": patient.get("OPID", "")
    }

    return render_template("patientView.html", patient=patient_data)


# -------------------- Doctor Login --------------------
@app.route("/doctorlogin", methods=["GET", "POST"])
def doctor_login():
    if request.method == "POST":
        opid = request.form.get("opid")
        password = request.form.get("password")

        if not opid or not password:
            return render_template("DoctorLogin.html", error="Please Enter Username and Password")

        doctor = doctors.find_one({"OPID": opid})
        if not doctor:
            return render_template("DoctorLogin.html", error="Invalid Username or Password")

        stored_hash = doctor.get("Password")
        if not stored_hash:
            return render_template("DoctorLogin.html", error="No Password Found")

        if check_password_hash(stored_hash, password):
            session["doctor_id"] = str(doctor["_id"])
            return redirect(url_for("doctor_view", id=str(doctor["_id"])))
        else:
            return render_template("DoctorLogin.html", error="Invalid Username or Password")

    return render_template("DoctorLogin.html")


# -------------------- Doctor View (All Patients) --------------------
@app.route("/doctors/<id>")
def doctor_view(id):
    if "doctor_id" not in session or session["doctor_id"] != id:
        return redirect(url_for("doctor_login"))

    doctor = doctors.find_one({"_id": ObjectId(id)})
    if not doctor:
        return "Doctor not found", 404

    all_patients = list(patients.find())

    doctor_data = {
        "first_name": doctor.get("First Name", ""),
        "last_name": doctor.get("Last Name", ""),
        "opid": doctor.get("OPID", "")
    }

    return render_template("DoctorView.html", doctor=doctor_data, patients=all_patients)


# -------------------- Doctor Add Record --------------------
@app.route("/add_record/<patient_id>", methods=["GET", "POST"])
def add_record(patient_id):
    if "doctor_id" not in session:
        return redirect(url_for("doctor_login"))

    patient = patients.find_one({"_id": ObjectId(patient_id)})
    if not patient:
        return "Patient not found", 404

    if request.method == "POST":
        new_record = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "blood_pressure": request.form.get("blood_pressure"),
            "temperature": request.form.get("temperature"),
            "notes": request.form.get("notes")
        }

        patients.update_one(
            {"_id": ObjectId(patient_id)},
            {"$push": {"records": new_record}}
        )

        return redirect(url_for("doctor_view", id=session["doctor_id"]))

    return render_template("add_record.html", patient=patient)


# -------------------- Patient View Records --------------------
@app.route("/view_records/<id>")
def view_records(id):
    if "patient_id" not in session or session["patient_id"] != id:
        return redirect(url_for("patient_login"))

    patient = patients.find_one({"_id": ObjectId(id)})
    if not patient:
        return "Patient not found", 404

    records = patient.get("records", [])
    return render_template("view_records.html", patient=patient, records=records)


# -------------------- Logout Routes --------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("patient_login"))

@app.route("/doctorlogout")
def doctor_logout():
    session.pop("doctor_id", None)
    return redirect(url_for("doctor_login"))


if __name__ == "__main__":
    app.run(debug=True)

