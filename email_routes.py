from flask import Blueprint, request, jsonify
from email_service import send_email   # import the function from email_service.py

email_bp = Blueprint("email_bp", __name__, url_prefix="/email")

@email_bp.route("/send-email", methods=["POST"])
def send_email_route():
    data = request.get_json()

    to_email = data.get("email")
    subject = data.get("subject")
    message = data.get("message")

    if not to_email or not subject or not message:
        return jsonify({"error": "Missing the required fields!"}), 400

    success = send_email(to_email, subject, message)

    if success:
        return jsonify({"status": "Email was sent successfully! ^_^"}), 200
    else:
        return jsonify({"status": "Failed to send the email :("}), 500
