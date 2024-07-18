import uuid
from clients.whatsapp_client import WhatsAppClient
from controllers.dialogflow_controller import DialogflowController
from database.repositories import UserRepository, ChatSessionRepository

class WhatsAppController:
    def __init__(self):
        self.whatsapp_client = WhatsAppClient()
        self.dialogflow_controller = DialogflowController()
        self.sessions = {}
        self.processed_message_ids = set()
    
    def process_text_message(self, chatbot_phone_number, recipient_number, recipient_message):
        post_job_phrases = ["post job", "post a job", "post new job", "post another job"]
        find_job_phrases = ["find job", "find a job", "find new job", "find another job"]

        user = UserRepository.get_user_by_phone_number(recipient_number)
        if recipient_message.lower() == "help":
            self.send_help_message(chatbot_phone_number, recipient_number)
            return
        
        if any(phrase in recipient_message.lower() for phrase in post_job_phrases + find_job_phrases):
            chat_session_id = str(uuid.uuid4())
            self.sessions[recipient_number] = chat_session_id

            if any(phrase in recipient_message.lower() for phrase in post_job_phrases):
                recipient_message = "Post Job"
                ChatSessionRepository.create_chat_session(chat_session_id, recipient_message, user.id)
            elif any(phrase in recipient_message.lower() for phrase in find_job_phrases):
                recipient_message = "Find Job"
                ChatSessionRepository.create_chat_session(chat_session_id, recipient_message, user.id)
                
            dialogflow_response = self.dialogflow_controller.handle_message(recipient_message, recipient_number, chat_session_id)
            self.whatsapp_client.send_whatsapp_message(chatbot_phone_number, recipient_number, dialogflow_response['simpleTextMessage'], 'text')
            return
        else:   
            chat_session_id = self.sessions.get(recipient_number)
            if not chat_session_id:
                chat_session = ChatSessionRepository.get_latest_chat_session_by_user(user.id)
                if chat_session:
                    chat_session_id = str(chat_session.id)
                    self.sessions[recipient_number] = chat_session_id
            dialogflow_response = self.dialogflow_controller.handle_message(recipient_message, recipient_number, chat_session_id)
            if "error" in dialogflow_response:
                response_message = "Something went wrong please try again"
                self.whatsapp_client.send_whatsapp_message(chatbot_phone_number, recipient_number, response_message)
            else:
                if 'replyBtnMessage' in dialogflow_response and dialogflow_response['replyBtnMessage'] is not None:
                    self.whatsapp_client.send_whatsapp_message(chatbot_phone_number, recipient_number, dialogflow_response['replyBtnMessage'], 'interactive')

                elif 'simpleTextMessage' in dialogflow_response and dialogflow_response['simpleTextMessage'] is not None:
                    self.whatsapp_client.send_whatsapp_message(chatbot_phone_number, recipient_number, dialogflow_response['simpleTextMessage'], 'text')
                else:
                    buttons = [
                        {
                            "type": "reply",
                            "reply": {
                                "id": "Post Job",
                                "title": "Post Job"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": "Find Job",
                                "title": "Find Job"
                            }
                        }
                    ]
                    response_message = (
                        f"*We encountered an issue processing your request.*\n\n"
                        f"Please try one of the following options:\n"
                        f'1️⃣ Post Job: Type "Post Job" to start posting a new job.\n'
                        f'2️⃣ Find Job: Type "Find Job" to search for available jobs.\n\n'
                        f"If you need any assistance, just type 'help'. 💬"
                    )
                    interactive_message = self.dialogflow_controller.create_button_message(response_message, buttons)
                    self.whatsapp_client.send_whatsapp_message(chatbot_phone_number, recipient_number, interactive_message, 'interactive')

    def handle_whatsapp_message(self, body):
        value = body["entry"][0]["changes"][0]["value"]
        message = value["messages"][0]
        recipient_number = value["contacts"][0]["wa_id"]
        recipient_name = value["contacts"][0]["profile"]['name']
        chatbot_phone_number = value["metadata"]["phone_number_id"]
        message_id = message["id"]

        user = UserRepository.get_user_by_phone_number(recipient_number)
        if not user:
            UserRepository.create_user(recipient_name, recipient_number)
            buttons = [
                {
                    "type": "reply",
                    "reply": {
                        "id": "Post Job",
                        "title": "Post Job"
                    }
                },
                {
                    "type": "reply",
                    "reply": {
                        "id": "Find Job",
                        "title": "Find Job"
                    }
                }
            ]

            response_message = (
                f"Hello, this is HOME SERVICE CHATBOT! 🏠🤖\n"
                f"Welcome, {recipient_name}! You have been successfully registered in our system. 🎉\n\n"
                f"✨ What would you like to do next?\n"
                f"1️⃣ Post Job\n"
                f"2️⃣ Find Job\n\n"
                f"If you need any assistance, just type 'help'. 💬"
            )
            interactive_message = self.dialogflow_controller.create_button_message(response_message, buttons)
            self.whatsapp_client.send_whatsapp_message(chatbot_phone_number, recipient_number, interactive_message, 'interactive')
            return {"status": "ok"}
        
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

    def send_help_message(self, chatbot_phone_number, recipient_number):
        help_message = (
            "📋 *Help Guide*\n\n"
            "🔹 *Post Job:* Type 'Post Job' to start posting a new job.\n\n"
            "🔹 *Find Job:* Type 'Find Job' to search for available jobs.\n\n"
            "🔹 *Check Status:* Type 'Check Status' to view the status of your jobs.\n\n"
            "🔹 *My Jobs:* Type 'My Jobs' to see a list of jobs you have posted or accepted.\n\n"
        )
        self.whatsapp_client.send_whatsapp_message(chatbot_phone_number, recipient_number, help_message, 'text')