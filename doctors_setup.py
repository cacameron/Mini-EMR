import os
import secrets
from pymongo import MongoClient
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
#this file ran once only for the db collection!!

#env variables loaded from .env
load_dotenv()

#connect mongo
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client["Mini_Emr_db"]
doctors = db["Doctors"]
patients = db["Patients"] #used to reference OPID uniqueness

#checks patients OPID
def generate_unique_opid(prefix="OPD"):
    while True:
        new_opid = f"OPD{secrets.randbelow(1000000):06d}"
        if not doctors.find_one({"OPID": new_opid}) and not patients.find_one({"OPID": new_opid}):
            return new_opid

all_updates = [] #used for summary of updates
for doctor in doctors.find({}):
    update_fields = {}
    #OPID added
    if "OPID" not in doctor:
        new_opid = generate_unique_opid(prefix="OPD")
        update_fields["OPID"] = new_opid
    
    #pwd hash
    pwd = doctor.get("Password")
    if pwd and not pwd.startswith("pbkdf2:sha256:"):
        hashed_pwd = generate_password_hash(pwd)
        update_fields["Password"] = hashed_pwd
    
    #update
    if update_fields:
        doctors.update_one(
            {"_id": doctor["_id"]},
            {"$set": update_fields}
        )
        summary = f"{update_fields.get('First Name', '')} {update_fields.get('Last Name', '')}: {str(update_fields)}"
        all_updates.append(summary)

print("Doctors setup has been sucessfully completed. Updates:")
for update in all_updates:
    print(update)