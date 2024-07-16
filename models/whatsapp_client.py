import requests
import io
from config import WHATSAPP_TOKEN, LANGUAGE

class WhatsAppClient:
    def __init__(self):
        self.whatsapp_token = WHATSAPP_TOKEN
        self.language = LANGUAGE
        
    def send_whatsapp_message(self, phone_number_id, from_number, message, interactive=False):
        headers = {
            "Authorization": f"Bearer {self.whatsapp_token}",
            "Content-Type": "application/json",
        }
        url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": from_number,
        }
        if interactive:
            data.update({"type": "interactive", "interactive": message["interactive"]})
        else:
            data.update(message)
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
