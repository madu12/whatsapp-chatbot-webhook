from models.dialogflow_client import DialogflowClient

class DialogflowController:
    def __init__(self):
        self.dialogflow_client = DialogflowClient()

    def handle_message(self, sender_message, recipient_number, chat_session_id=None):
        response = self.dialogflow_client.detect_intent(sender_message, recipient_number, chat_session_id)
        if response:
            return self.process_dialogflow_response(response.response_messages)
        else:
            return {"error": "Failed to detect intent"}
        
    def process_dialogflow_response(self, fulfillment_messages):
        try:
            reply_btn_message = None
            simple_text_message = None

            # Process payload messages for buttons and lists
            payload_messages = [message for message in fulfillment_messages if hasattr(message, 'payload') and message.payload is not None]
            text_message = [message for message in fulfillment_messages if 'text' in message.text]
            
            if payload_messages:
                buttons, payload_text = self.process_payload_messages(payload_messages)

                if not text_message:
                    payload_text_message = payload_text
                else:
                    payload_text_message = text_message[0].text.text[0]

                if buttons:
                    reply_btn_message = self.create_button_message(payload_text_message, buttons)

            if not reply_btn_message and text_message:
                if not text_message:
                    None
                else:
                    simple_text_message = text_message[0].text.text[0]
            return {
                "replyBtnMessage": reply_btn_message,
                "simpleTextMessage": simple_text_message
            }
        except Exception as e:
            print(f"Error processing Dialogflow response: {e}")
            raise e

    def process_payload_messages(self, payload_messages):
        buttons = []
        payload_text = ''

        for payload_message in payload_messages:
            payload_dict = dict(payload_message.payload)
            payload_richContent = payload_dict['richContent']
            
            for item in payload_richContent:
                item_dict = dict(item)
                
                if 'text' in item_dict:
                    payload_text = item_dict['text']
                elif 'options' in item_dict and item_dict['type'] == 'chips':
                    for option in item_dict['options']:
                        buttonText = option['text']
                        anchorHref = option['anchor']['href'] if 'anchor' in option and 'href' in option['anchor'] else ""
                        if anchorHref:
                            buttons.append({
                                "type": "url",
                                "url": anchorHref,
                                "title": buttonText
                            })
                        else:
                            buttons.append({
                                "type": "reply",
                                "reply": {
                                    "id": buttonText,
                                    "title": buttonText
                                }
                            })
                    
        return buttons, payload_text

    def create_button_message(self, text, buttons):
        for button in buttons:
            if button['type'] == 'url':
                return {
                    "interactive": {
                        "type": "cta_url",
                        "body": {"text": text},
                        "action": {
                            "name": "cta_url",
                            "parameters": {
                                "url": button['url'],
                                "display_text": button['title']
                            }
                        }
                    }
                }
        return {
            "interactive": {
                "type": "button",
                "body": {"text": text},
                "action": {"buttons": buttons}
            }
        }
