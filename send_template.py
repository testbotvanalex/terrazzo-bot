from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = 'whatsapp:+14155238886'  # Twilio sandbox
user_number = 'whatsapp:+476322337'  # bv. whatsapp:+324....

client = Client(account_sid, auth_token)

message = client.messages.create(
    from_=twilio_number,
    to=user_number,
    content_sid="HXb9136924a3b109b62556bbdcf6d80ae0"
)

print("✅ Verzonden:", message.sid)