import requests
from config import WHATSAPP_TOKEN, LANGUAGE

class WhatsAppClient:
    def __init__(self):
        """
        Initialize the WhatsAppClient with the necessary credentials.
        """
        self.whatsapp_token = WHATSAPP_TOKEN
        self.language = LANGUAGE

    def send_whatsapp_message(self, phone_number_id, from_number, message, message_type='text'):
        """
        Send a message through WhatsApp API.

        Args:
            phone_number_id (str): The phone number ID of the chatbot.
            from_number (str): The phone number of the recipient.
            message (str): The message to send.
            message_type (str): The type of message ('text' or 'interactive').

        Raises:
            requests.exceptions.RequestException: If the request to WhatsApp API fails.
        """
        try:
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
            if message_type == 'interactive':
                data.update({"type": "interactive", "interactive": message["interactive"]})
            else:
                data.update({"type": "text", "text": {"preview_url": False, "body": message}})

            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except Exception as err:
            print(f"Error occurred: {err}")
