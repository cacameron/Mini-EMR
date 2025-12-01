import os
from flask import Blueprint, request, render_template_string
from bson.objectid import ObjectId
from datetime import datetime

def create_file_upload_blueprint(db):
    uploads_bp = Blueprint("uploads_bp", __name__)

    records = db["Records"]
    patients = db["Patients"]

    UPLOAD_FOLDER = "uploads"
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # ----------------------------
    # Upload Page
    # ----------------------------
    @uploads_bp.route("/upload/<patient_id>", methods=["GET"])
    def upload_page(patient_id):
        patient = patients.find_one({"_id": ObjectId(patient_id)})
        if not patient:
            return "Patient not found", 404

        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Upload Medical File</title>
            <style>
                body { font-family: Arial; padding: 40px; }
                .upload-box {
                    padding: 20px;
                    border: 2px dashed #555;
                    border-radius: 10px;
                    width: 300px;
                    text-align: center;
                }
                button {
                    margin-top: 10px;
                    padding: 10px 20px;
                    background: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                }
            </style>
        </head>
        <body>
            <h2>Upload a File for {{patient_name}}</h2>
            <form action="/upload_file/{{patient_id}}" method="POST" enctype="multipart/form-data">
                <div class="upload-box">
                    <input type="file" name="uploaded_file" required><br><br>
                    <button type="submit">Upload</button>
                </div>
            </form>
        </body>
        </html>
        """

        return render_template_string(html,
            patient_name=f"{patient['First Name']} {patient['Last Name']}",
            patient_id=str(patient_id)
        )

    # ----------------------------
    # File Upload Handler
    # ----------------------------
    @uploads_bp.route("/upload_file/<patient_id>", methods=["POST"])
    def upload_file(patient_id):

        if "uploaded_file" not in request.files:
            return "No file provided."

        file = request.files["uploaded_file"]

        if file.filename == "":
            return "No file selected."

        filename = file.filename
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)

        # Store metadata
        records.insert_one({
            "patient_id": ObjectId(patient_id),
            "type": "file_upload",
            "file_name": filename,
            "file_path": save_path,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })

        return f"<h2>File uploaded successfully!</h2><p>Saved as: {filename}</p>"

    return uploads_bp
