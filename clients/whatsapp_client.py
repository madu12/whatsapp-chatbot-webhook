import requests
from config import WHATSAPP_TOKEN, LANGUAGE, WHATSAPP_CHATBOT_PHONE_NUMBER
from asgiref.sync import sync_to_async

class WhatsAppClient:
    def __init__(self):
        """
        Initialize the WhatsAppClient with the necessary credentials.
        """
        self.whatsapp_token = WHATSAPP_TOKEN
        self.language = LANGUAGE
        self.whatsapp_chatbot_phone_number = WHATSAPP_CHATBOT_PHONE_NUMBER

    async def send_whatsapp_message(self, to_number, message, message_type='text'):
        """
        Send a message through WhatsApp API.

        Args:
            to_number (str): The phone number of the recipient.
            message (str): The message to send.
            message_type (str): The type of message ('text' or 'interactive').

        Returns:
            bool: True if the message was sent successfully, False otherwise.

        Raises:
            requests.exceptions.RequestException: If the request to WhatsApp API fails.
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.whatsapp_token}",
                "Content-Type": "application/json",
            }
            url = f"https://graph.facebook.com/v19.0/{self.whatsapp_chatbot_phone_number}/messages"
            data = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to_number,
            }
            if message_type == 'interactive':
                data.update({"type": "interactive", "interactive": message["interactive"]})
            else:
                data.update({"type": "text", "text": {"preview_url": False, "body": message}})

            # Sending the request asynchronously
            response = await sync_to_async(requests.post)(url, json=data, headers=headers)

            # Log the response status and text for debugging
            if response.status_code == 200:
                return True
            else:
                print(f"Failed to send message: {response.status_code} - {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return False
        except Exception as err:
            print(f"Error occurred: {err}")
            return False
