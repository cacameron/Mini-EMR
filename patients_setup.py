import os
import random
import string
from pymongo import MongoClient
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

#env variables loaded from .env
load_dotenv()

#connect mongo
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client["Mini_Emr_db"]
patients = db["Patients"]

#Generate unique OPID
def generate_unique_opid():
    while True:
        opid = "OP" + ''.join(random.choices(string.digits, k=6))
        if not patients.find_one({"OPID": opid}):
            return opid

#Update for all patients in db
for patient in patients.find({}):
    updates = {}
    #generate opid if missing
    if "OPID" not in patient:
        new_opid = generate_unique_opid()
        updates["OPID"] = new_opid
        print(f"Generated OPID {new_opid} for {patient.get('First Name', '')} {patient.get('Last Name', '')}")
    #hash pwd if none
    password = patient.get("Password")
    if password and not password.startswith("pbkdf2:sha256:"):
        hashed_pw = generate_password_hash(password)
        updates["Password"] = hashed_pw
        print(f"Hashed password for {patient.get('Email', '')}")
    #update
    if updates:
        patients.update_one({"_id": patient["_id"]}, {"$set": updates})
print("All patient records have been succesfully updated! ^_^")