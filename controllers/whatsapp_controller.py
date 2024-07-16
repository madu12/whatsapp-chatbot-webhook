# controllers/whatsapp_controller.py

from models.whatsapp_client import WhatsAppClient
from controllers.dialogflow_controller import DialogflowController

class WhatsAppController:
    def __init__(self):
        self.whatsapp_client = WhatsAppClient()
        self.dialogflow_controller = DialogflowController()
        self.processed_message_ids = set()  # Use a set to track processed message IDs
    
    def process_text_message(self, chatbot_phone_number, recipient_number, recipient_message):
        dialogflow_response = self.dialogflow_controller.handle_message(recipient_message, recipient_number)
        if "error" in dialogflow_response:
            response_message = "Something went wrong please try again"
            self.whatsapp_client.send_whatsapp_message(chatbot_phone_number, recipient_number, response_message)
        else:
            if 'replyBtnMessage' in dialogflow_response and dialogflow_response['replyBtnMessage'] is not None:
                self.whatsapp_client.send_whatsapp_message(chatbot_phone_number, recipient_number, dialogflow_response['replyBtnMessage'], 'interactive')

            elif 'simpleTextMessage' in dialogflow_response and dialogflow_response['simpleTextMessage'] is not None:
                self.whatsapp_client.send_whatsapp_message(chatbot_phone_number, recipient_number, dialogflow_response['simpleTextMessage'], 'text')
            else:
                response_message = "No valid response received from Dialogflow"
                self.whatsapp_client.send_whatsapp_message(chatbot_phone_number, recipient_number, response_message)

    def handle_whatsapp_message(self, body):
        value = body["entry"][0]["changes"][0]["value"]
        message = value["messages"][0]
        recipient_number = value["contacts"][0]["wa_id"]
        chatbot_phone_number = value["metadata"]["phone_number_id"]
        message_id = message["id"]

        if message_id in self.processed_message_ids:
            return {"status": "ok"}

        self.processed_message_ids.add(message_id)

        if message["type"] == "text":
            recipient_message = message["text"]["body"]
            self.process_text_message(chatbot_phone_number, recipient_number, recipient_message)
        elif message["type"] == "interactive":
            interactive_message = message["interactive"]["button_reply"]["id"]
            self.process_text_message(chatbot_phone_number, recipient_number, interactive_message)
        else:
            response_message = 'This chatbot only supports text and interactive messages.'
            self.whatsapp_client.send_whatsapp_message(chatbot_phone_number, recipient_number, response_message)
            
        return {"status": "ok"}
