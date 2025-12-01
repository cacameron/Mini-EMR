import os
import requests
from dotenv import load_dotenv

#load enviroment variables 
load_dotenv()

# Load API Configuration
API_KEY = os.getenv('MAILEROO_API_KEY') 
API_URL = os.getenv('MAILEROO_API_URL')
SENDER_EMAIL = os.getenv('MAILEROO_SENDER_EMAIL')  
SENDER_NAME = os.getenv('MAILEROO_SENDER_NAME')  


def send_email(to_email: str, subject: str, message: str):
    """Send an email using the Maileroo API."""

    payload = {
        'from': f'{SENDER_NAME} <{SENDER_EMAIL}>',
        'to': to_email,
        'subject': subject,
        'plain': message,
    }

    try:
        # API Request
        response = requests.post(API_URL, headers={'X-API-Key': API_KEY}, data=payload)
        response_json = response.json()
        if response.status_code == 200 and response.json().get('success'):
            print("Email sent successfully to {to_email}!")
            return True
        else:
            error_message = response_json.get('message', 'Unknown error')
            print(f"Failed to send email to {to_email}: {error_message}")
            return False
    except Exception as e:
        print(f"Error sending email to {to_email}: {e}")
        return False

#example
if __name__ == "__main__":
    send_email("recipient@example.com", "Test Email", "This is a test email from Maileroo.")
