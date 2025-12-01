# -------------------- appointments.py --------------------
from flask import Blueprint, render_template, request, redirect, url_for, session
from bson.objectid import ObjectId
from datetime import datetime
from email_service import send_email


#blueprint
def create_appointments_blueprint(db, patients_col, doctors_col, nurses_col):
    appointments_bp = Blueprint("appointments", __name__, url_prefix="/appointments")
    
    #collections  in mongodb
    patients = patients_col
    doctors = doctors_col
    nurses = nurses_col
    appointments = db["Appointments"]

   # -------------------- VIEW APPOINTMENTS (everyone) --------------------
    @appointments_bp.route("/")
    def view_appointments():
        """View appointments depending on who is logged in."""
        if "doctor_id" in session:
            role = "doctor"
            user_appointments = list(appointments.find({"doctor_id": ObjectId(session["doctor_id"])}))
        elif "nurse_id" in session:
            role = "nurse"
            user_appointments = list(appointments.find({"nurse_id": ObjectId(session["nurse_id"])}))
        elif "patient_id" in session:
            role = "patient"
            user_appointments = list(appointments.find({"patient_id": ObjectId(session["patient_id"])}))
        else:
            return redirect(url_for("index"))

        # Add readable info for each appointment
        for appt in user_appointments:
            patient = patients.find_one({"_id": ObjectId(appt["patient_id"])})
            doctor = doctors.find_one({"_id": ObjectId(appt["doctor_id"])})
            appt["patient_name"] = f"{patient['First Name']} {patient['Last Name']}" if patient else "Unknown"
            appt["doctor_name"] = f"{doctor['First Name']} {doctor['Last Name']}" if doctor else "Unknown"

        return render_template("appointments.html", appointments=user_appointments, role=role)

#----------------------PATIENT ROUTES SECTION-----------------------

    #Self Booking
    @appointments_bp.route("/book/<patient_id>", methods=["GET", "POST"])
    def book_appointment(patient_id):

        if "patient_id" not in session or session["patient_id"]!=patient_id:
            return redirect(url_for("patient_login"))
        
        patient = patients.find_one({"_id": ObjectId(patient_id)})
        if not patient:
            return "Patient not found", 404
        
        assigned_doctor = patient.get("AssignedDoctorID")
        
        if request.method == "POST":
            date = request.form["date"]
            time = request.form["time"]
            doctor_id = request.form.get("doctor_id") or assigned_doctor
            reason = request.form.get("reason", "")
            appointment_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")

            #checks that patient picked doctor
            if not doctor_id:
                return "Please select a doctor from the list."
            
            #Check for double booking
            conflict = appointments.find_one({
                "doctor_id": ObjectId(doctor_id),
                "datetime": appointment_datetime,
                "status": {"$ne": "denied"}
            })

            if conflict:
                return "This time slot is already booked for your doctor.", 409
            
            #insert appointment
            appointments.insert_one({
                "patient_id": ObjectId(patient_id),
                "doctor_id": ObjectId(doctor_id),
                "datetime": appointment_datetime,
                "reason": reason,
                "status": "pending",
                "created_by": f"{patient['First Name']} {patient['Last Name']}",
                "created_role": "patient",
                "created_at": datetime.now()
            })

            return redirect(url_for("appointments.view_my_appointments", patient_id=patient_id))
        
        #display booking form
        doctors_list = list(doctors.find())
        return render_template(
            "book_appointment.html",
            patient=patient,
            assigned_doctor=assigned_doctor,
            doctors_list=doctors_list
        )


    #View Appointments
    @appointments_bp.route("/view/<patient_id>")
    def view_my_appointments(patient_id):
        if "patient_id" not in session or session["patient_id"]!=patient_id:
            return redirect(url_for("patient_login"))
        
        patient = patients.find_one({"_id": ObjectId(patient_id)})
        my_appointments = list(appointments.find({"patient_id": ObjectId(patient_id)}))

        return render_template("patient_appointment_view.html",
                            patient=patient, appts=my_appointments)

    #Edit Pending Appointments
    @appointments_bp.route("/edit/<appt_id>", methods=["GET", "POST"])
    def edit_appointment(appt_id):

        appt = appointments.find_one({"_id": ObjectId(appt_id)})
        if not appt:
            return "Appointment Not Found", 404
        
        if "patient_id" not in session or session["patient_id"] != str(appt["patient_id"]):
            return redirect(url_for("patient_login"))
        
        if appt["status"] != "pending":
            return "Only appointments that are pending can be edited.", 403
        
        patient = patients.find_one({"_id": appt["patient_id"]})

        if request.method == "POST":
            date = request.form["date"]
            time = request.form["time"]
            reason = request.form["reason"]
            new_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")

            #check for double booking
            conflict = appointments.find_one({
                "doctor_id": appt["doctor_id"],
                "datetime": new_dt,
                "_id": {"$ne": ObjectId(appt_id)},
                "status": {"$ne": "denied"}
            })

            if conflict:
                return render_template("edit_appointment.html",
                    appt=appt,
                    patient=patient,
                    error="This time slot is already booked."
                )
            
            #update appointment
            appointments.update_one(
                {"_id": ObjectId(appt_id)},
                {"$set": {"datetime": new_dt, "reason": reason}}
            )

            return redirect(url_for("appointments.view_my_appointments",
                                    patient_id=str(appt["patient_id"])))
        
        return render_template("edit_appointment.html", appt=appt, patient=patient)

#-----------------------STAFF ROUTES SECTION-------------------------

    #view pending appointments
    @appointments_bp.route("/pending")
    def view_pending():
        #Doctor or Nurse
        if "doctor_id" not in session and "nurse_id" not in session:
            return redirect(url_for("index"))
        
        pending = list(appointments.find({"status": "pending"}).sort("datetime", 1))

        return render_template("appointments_pending.html", pending=pending)

    #approve appointments
    @appointments_bp.route("/approve/<appt_id>", methods=["POST"])
    def approve_appointment(appt_id):
        if "doctor_id" not in session and "nurse_id" not in session:
            return redirect(url_for("index"))
        
        appt = appointments.find_one({"_id": ObjectId(appt_id)})
        if not appt:
            return "Appointment Not Found", 404
        
        #double booking check
        conflict = appointments.find_one({
            "doctor_id": appt["doctor_id"],
            "datetime": appt["datetime"],
            "_id": {"$ne": ObjectId(appt_id)},
            "status": "approved"
        })

        if conflict:
            return "Unable to approve. Doctor is already booked!"
        
        #update status
        appointments.update_one(
            {"_id": ObjectId(appt_id)},
            {"$set": {"status": "approved"}}
        )

        patient = patients.find_one({"_id": appt["patient_id"]})

        send_email(
            to_email=patient["Email"],
            subject="Appointment Approved",
            message=f"Your appointment on {appt['datetime']} has been approved."
        )
        
        return redirect(url_for("appointments.view_pending"))

    #deny appointment
    @appointments_bp.route("/deny/<appt_id>", methods=["POST"])
    def deny_appointment(appt_id):
        if "doctor_id" not in session and "nurse_id" not in session:
            return redirect(url_for("index"))
        
        appt = appointments.find_one({"_id": ObjectId(appt_id)})
        if not appt:
            return "Appointment Not Found", 404
        
        appointments.update_one(
            {"_id": ObjectId(appt_id)},
            {"$set": {"status": 'denied'}}
        )

        patient = patients.find_one({"_id": appt["patient_id"]})

        send_email(
            to_email=patient["Email"],
            subject="Appointment Denied.",
            message=f"Your appointment on {appt['datetime']} has been denied."
        )
        
        return redirect(url_for("appointments.view_pending"))


 
    # -------------------- STAFF ADD APPOINTMENT --------------------
    @appointments_bp.route("/add_appointment/<patient_id>", methods=["GET", "POST"])
    def add_appointment(patient_id):
        """Add a new appointment for a patient (Doctor/Nurse only)."""
        if "doctor_id" not in session and "nurse_id" not in session:
            return redirect(url_for("index"))

        patient = patients.find_one({"_id": ObjectId(patient_id)})
        if not patient:
            return "Patient not found", 404

        #doctors list for nurses to pick from
        doctors_list = list(doctors.find())
        
        if request.method == "POST":
            date = request.form["date"]
            time = request.form["time"]
            reason = request.form.get("reason", "")
            notes = request.form.get("notes", "")
            appointment_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")

            if "doctor_id" in session:
                creator_id = session["doctor_id"]
                creator_role = "doctor"
                creator = doctors.find_one({"_id": ObjectId(creator_id)})
                created_by = f"Dr. {creator['First Name']} {creator['Last Name']}"
            
                #doctor assignment
                doctor_id = ObjectId(creator_id)

            else:
                creator_id = session["nurse_id"]
                creator_role = "nurse"
                creator = nurses.find_one({"_id": ObjectId(creator_id)})
                created_by = f"Nurse {creator['First Name']} {creator['Last Name']}"

                #nurse chooses doctor from form
                doctor_id = ObjectId(request.form["doctor_id"])
            
            #check for double booking
            conflict = appointments.find_one({
                "doctor_id": doctor_id,
                "datetime": appointment_datetime,
                "status": {"$ne": "denied"}
            })

            if conflict:
                return "This doctor is already booked for this time slot!"


            new_appointment = {
                "doctor_id": doctor_id,
                "nurse_id": ObjectId(session ["nurse_id"]) if "nurse_id" in session else None,
                "patient_id": ObjectId(patient_id),
                "datetime": appointment_datetime,
                "reason": reason,
                "notes": notes,
                "status": "approved",
                "created_by": created_by,
                "creator_role": creator_role,
                "created_at": datetime.now()
            }

            appointments.insert_one(new_appointment)
            return redirect(url_for("appointments.view_appointments"))

        return render_template("add_appointment.html", patient=patient, doctors_list=doctors_list)

    # -------------------- DELETE APPOINTMENT --------------------
    @appointments_bp.route("/delete_appointment/<appointment_id>")
    def delete_appointment(appointment_id):
        """Delete an appointment (only Doctor/Nurse)."""
        if "doctor_id" not in session and "nurse_id" not in session:
            return redirect(url_for("index"))

        appointments.delete_one({"_id": ObjectId(appointment_id)})
        return redirect(url_for("appointments.view_appointments"))

    return appointments_bp
