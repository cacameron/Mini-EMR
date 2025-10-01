import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

#env vars loaded from .env
load_dotenv()
#get MongoDB uri
mongo_uri = os.getenv("MONGO_URI")

#connect to MongoDB, 5s timeout so no looping forever
client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
db = client["Mini_Emr_db"]
patients_collection = db["Patients"]

#test connect
try:
    client.admin.command("ping")
    print("MongoDB connection success")
except ServerSelectionTimeoutError as e:
    print("MongoDB connection failed:", e)
    exit(1)
#retrieve patients w/o id
patients = list(patients_collection.find({}, {"_id": 0}))
#print patients
if patients:
    print("Patients in database:")
    for patient in patients:
        print(patient)
else:
    print("No patients found")


#access collections??
#patients = ["Patients"]
#doctors = ["Doctors"]
#admins = db["Admins"]

#print("Yay, Connected to MongoDB!")