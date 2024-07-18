from clients.dialogflow_client import DialogflowClient
import datetime

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

            # Process payload messages for buttons
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

    def webhook_response(self, text_response, payload_response, parameters):
        response = {
            "fulfillment_response": {},
            "session_info": {}
        }

        if text_response:
            response["fulfillment_response"]["messages"] = [
                {
                    "text": {
                        "text": [text_response]
                    }
                }
            ]

        if payload_response:
            response["fulfillment_response"]["messages"] = [
                {
                    "payload": payload_response
                }
            ]

        if parameters:
            response["session_info"]["parameters"] = parameters

        return response
    
    def handle_dialogflow_webhook(self, body):
        if not body:
            return {"status": "error", "message": "Empty or undefined message received."}

        try:
            text = body.get("text")
            session_info = body.get("sessionInfo")
            fulfillment_info = body.get("fulfillmentInfo")
            page_info = body.get("pageInfo")

            if not session_info:
                return {"status": "error", "message": "Missing session information."}

            parameters = session_info.get("parameters")
            session = session_info.get("session")
            session_id = session.split("/")[-1]
            recipient_number = session_id.split("&")[0]
            chat_session_id = session_id.split("&")[1] if "&" in session_id else None

            if fulfillment_info and "tag" in fulfillment_info:
                tag = fulfillment_info["tag"]

                if tag == 'validateCollectedPostJobData' or tag == 'validateCollectedFindJobData':
                    return self.process_post_job_data(parameters, text)

                if tag == 'postJobDataConfirmation':
                    return self.post_job_data_confirmation(parameters)
                
                if tag == 'postJobDataSave':
                    return self.post_job_data_save(parameters)

            return {"status": "error", "message": "No valid tag found in fulfillment info."}
        except Exception as e:
            print(f"Error processing Dialogflow webhook: {e}")
            return {"status": "error", "message": str(e)}
        
    def process_post_job_data(self,parameters, text = None):
        try:
            json_parameters = {}
            if not parameters.get('job_category') and text:
                get_job_category = self.get_job_category(text)

                if get_job_category:
                    json_parameters["job_category"] = get_job_category
                
            if parameters.get('date_time') and (not parameters.get('date') or not parameters.get('time')):
                date_time = parameters.get('date_time')
                date_param = {
                    "year": int(date_time['year']),
                    "month": int(date_time['month']),
                    "day": int(date_time['day'])
                } if 'year' in date_time else None
                
                time_param = {
                    "hours": int(date_time['hours']),
                    "minutes": int(date_time['minutes']),
                    "seconds": int(date_time['seconds']),
                    "nanos": int(date_time['nanos'])
                } if 'hours' in date_time else None
                
                if date_param:
                    json_parameters["date"] = date_param
                if time_param:
                    json_parameters["time"] = time_param
            
            if parameters.get('zip_code'):
                zip_code = parameters.get('zip_code')
                valid_zip_code, zip_code_data = self.is_valid_zip_code(zip_code)
                
                if not valid_zip_code:
                    json_parameters["zip_code"] = None
                else:
                    json_parameters["location_data"] = f"{zip_code_data['city']}, {zip_code_data['state_id']}"

            if parameters.get('amount'):
                if float(parameters['amount']['amount']) < 10:
                    json_parameters["amount"] = None
                    return self.webhook_response("Minimum price is $10 for this job.", None, json_parameters)
                
            return self.webhook_response(None, None, json_parameters)

        except Exception as e:
            print(f"Error processing job data: {e}")
            return {"message": "Error processing job data.", "status": 500}

    def post_job_data_confirmation(self, parameters):
        try:
            job_category = parameters.get("job_category", "N/A")
            job_date = parameters.get("date", {})
            job_time = parameters.get("time", {})
            job_location = parameters.get("location_data", "N/A")
            amount = parameters.get("amount", {})
            posting_fee = parameters.get("posting_fee")

            # Format job date and time
            job_date_str = f"{int(job_date.get('month'))}/{int(job_date.get('day'))}/{int(job_date.get('year'))}"
            job_time_obj = datetime.time(
                hour=int(job_time.get('hours', 0)),
                minute=int(job_time.get('minutes', 0)),
                second=int(job_time.get('seconds', 0))
            )
            job_time_str = job_time_obj.strftime("%I:%M %p")

            # Format amount
            amount_str = f"${amount.get('amount'):.2f}" if amount else "N/A"

            # Create a response message
            response_message = (
                f"*Please confirm the details of your job posting:*\n\n"
                f"Job Category: {job_category.capitalize()}\n"
                f"Date: {job_date_str}\n"
                f"Time: {job_time_str}\n"
                f"Location: {job_location}\n"
                f"Amount: {amount_str}\n"
                f"Posting Fee: ${posting_fee:.2f}\n\n"
                f"Do you want to post this job?"
            )

            payloadResponse = {
                "richContent": [
                    {
                        "text": response_message
                    },
                    {
                        "type": "chips",
                        "options": [
                            {
                                "text": "Yes",
                            },
                            {
                                "text": "No",
                            }
                        ]
                    }
                ]
            }
            return self.webhook_response(None, payloadResponse, None)
        
        except Exception as e:
            print(f"Error saving job data: {e}")
            return {"error": "Failed to save job data"}
        
    def get_job_category(self, text):
        return 'pet care'
        
    def is_valid_zip_code(self, zip_code):
        return True, {"city": "San Diego", "state_id": "CA"}