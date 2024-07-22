from clients.dialogflow_client import DialogflowClient
import datetime
from database.repositories import ChatSessionRepository, JobRepository, CategoryRepository, UserRepository
from clients.stripe_client import StripeClient
import requests
from config import GOOGLE_MAPS_API_KEY, CLASSIFICATION_MODEL_API_URL, CLASSIFICATION_MODEL_API_KEY
from asgiref.sync import sync_to_async
import logging


class DialogflowController:
    def __init__(self):
        """
        Initialize the DialogflowController with the necessary clients.
        """
        self.dialogflow_client = DialogflowClient()
        self.stripe_client = StripeClient()
        self.api_key = GOOGLE_MAPS_API_KEY

    async def handle_message(self, sender_message, recipient_number, chat_session_id=None):
        """
        Handle the incoming message by detecting the intent using Dialogflow.

        Args:
            sender_message (str): The message sent by the user.
            recipient_number (str): The phone number of the recipient.
            chat_session_id (str, optional): The chat session ID. Defaults to None.

        Returns:
            dict: The processed response from Dialogflow.
        """
        response = await self.dialogflow_client.detect_intent(sender_message, recipient_number, chat_session_id)
        if response:
            return await self.process_dialogflow_response(response.response_messages)
        else:
            return {"error": "Failed to detect intent"}

    async def process_dialogflow_response(self, fulfillment_messages):
        """
        Process the response messages from Dialogflow.

        Args:
            fulfillment_messages (list): The list of fulfillment messages from Dialogflow.

        Returns:
            dict: The processed messages in a structured format.
        """
        try:
            reply_btn_message = None
            simple_text_message = None

            # Process payload messages for buttons
            payload_messages = [message for message in fulfillment_messages if hasattr(message, 'payload') and message.payload is not None]
            text_message = [message for message in fulfillment_messages if 'text' in message.text]

            if payload_messages:
                buttons, payload_text = await self.process_payload_messages(payload_messages)

                if not text_message:
                    payload_text_message = payload_text
                else:
                    payload_text_message = text_message[0].text.text[0]

                if buttons:
                    reply_btn_message = await self.create_button_message(payload_text_message, buttons)

            if not reply_btn_message and text_message:
                simple_text_message = text_message[0].text.text[0] if text_message else None

            return {
                "replyBtnMessage": reply_btn_message,
                "simpleTextMessage": simple_text_message
            }
        except Exception as e:
            print(f"Error processing Dialogflow response: {e}")
            raise e

    async def process_payload_messages(self, payload_messages):
        """
        Process payload messages to extract buttons and text.

        Args:
            payload_messages (list): List of payload messages.

        Returns:
            tuple: A tuple containing buttons and payload text.
        """
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

    async def create_button_message(self, text, buttons):
        """
        Create a button message for WhatsApp interactive messages.

        Args:
            text (str): The text to display with the buttons.
            buttons (list): The list of buttons.

        Returns:
            dict: The interactive message with buttons.
        """
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

    async def webhook_response(self, text_response, payload_response, parameters):
        """
        Generate a webhook response for Dialogflow.

        Args:
            text_response (str): The text response.
            payload_response (dict): The payload response.
            parameters (dict): The session parameters.

        Returns:
            dict: The structured webhook response.
        """
        try:
            response = {
                "fulfillment_response": {
                    "messages": []
                },
                "session_info": {
                    "parameters": {}
                }
            }

            if text_response:
                response["fulfillment_response"]["messages"].append(
                    {
                        "text": {
                            "text": [text_response]
                        }
                    }
                )

            if payload_response:
                response["fulfillment_response"]["messages"].append(
                    {
                        "payload": payload_response
                    }
                )

            if parameters:
                response["session_info"]["parameters"] = parameters

            # Remove "session_info" if no parameters were added
            if not response["session_info"]["parameters"]:
                del response["session_info"]

            # Remove "fulfillment_response" if no messages were added
            if not response["fulfillment_response"]["messages"]:
                del response["fulfillment_response"]

            return response

        except Exception as e:
            raise e


    async def handle_dialogflow_webhook(self, body):
        """
        Handle the webhook request from Dialogflow.

        Args:
            body (dict): The request body from Dialogflow.

        Returns:
            dict: The response to be sent back to Dialogflow.
        """
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
                print("Processing tag:", tag)  # Logging the tag being processed

                if tag == 'validateCollectedPostJobData' or tag == 'validateCollectedFindJobData':
                    webhook_response = await self.process_post_job_data(parameters, text)
                    print("Processed post job data response:", webhook_response)
                    return webhook_response

                if tag == 'postJobDataConfirmation':
                    response = await self.post_job_data_confirmation(parameters)
                    print("Post job data confirmation response:", response)
                    return response

                if tag == 'postJobDataSave':
                    response = await self.post_job_data_save(parameters, recipient_number, chat_session_id)
                    print("Post job data save response:", response)
                    return response

            return {"status": "error", "message": "No valid tag found in fulfillment info."}
        except Exception as e:
            print(f"Error processing Dialogflow webhook: {e}")
            return {"status": "error", "message": str(e)}

    async def process_post_job_data(self, parameters, text=None):
        """
        Process the collected post job data.

        Args:
            parameters (dict): The parameters from Dialogflow.
            text (str, optional): Additional text to process. Defaults to None.

        Returns:
            dict: The webhook response with updated parameters.
        """
        try:
            json_parameters = {}

            # if 'job_description' in parameters and parameters['job_description']:
            #     if text and text not in parameters['job_description']:
            #         json_parameters["job_description"] = f"{parameters['job_description']} {text}".strip()
            #     else:
            #         json_parameters["job_description"] = parameters['job_description']
            # else:
            #     json_parameters["job_description"] = text

            # if not parameters.get('job_category') and text:
            #     get_job_category = await self.get_job_category(text)
            #     if get_job_category:
            #         json_parameters["job_category"] = get_job_category

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

            # if parameters.get('zip_code'):
            #     zip_code = parameters.get('zip_code')
            #     valid_zip_code, zip_code_data = await self.is_valid_zip_code(zip_code)
            #     if not valid_zip_code:
            #         json_parameters["zip_code"] = None
            #     else:
            #         json_parameters["location_data"] = f"{zip_code_data['city']}, {zip_code_data['state_id']}"

            if parameters.get('amount'):
                if float(parameters['amount']['amount']) < 10:
                    json_parameters["amount"] = None
                    return await self.webhook_response("Minimum price is $10 for this job.", None, json_parameters)
            return await self.webhook_response(None, None, json_parameters)

        except Exception as e:
            print(f"Error processing job data: {e}")
            return {"message": "Error processing job data.", "status": 500}

    async def post_job_data_confirmation(self, parameters):
        """
        Confirm the details of the job posting.

        Args:
            parameters (dict): The parameters from Dialogflow.

        Returns:
            dict: The webhook response for job confirmation.
        """
        try:
            job_category = parameters.get("job_category", "N/A")
            job_description = parameters.get("job_description", "N/A")
            job_date = parameters.get("date", {})
            job_time = parameters.get("time", {})
            job_location = parameters.get("location_data", "N/A")
            amount = parameters.get("amount", {})
            posting_fee = parameters.get("posting_fee")
            job_date_str = f"{int(job_date.get('month'))}/{int(job_date.get('day'))}/{int(job_date.get('year'))}"
            job_time_obj = datetime.time(
                hour=int(job_time.get('hours', 0)),
                minute=int(job_time.get('minutes', 0)),
                second=int(job_time.get('seconds', 0))
            )
            job_time_str = job_time_obj.strftime("%I:%M %p")
            amount_str = f"${amount.get('amount'):.2f}" if amount else "N/A"

            # Create a response message
            response_message = (
                f"✨ *Please confirm the details of your job posting:* ✨\n\n"
                f"  🔹 *Job Category:* {job_category.capitalize()}\n"
                f"  🔹 *Date:* {job_date_str}\n"
                f"  🔹 *Time:* {job_time_str}\n"
                f"  🔹 *Location:* {job_location}\n"
                f"  🔹 *Amount:* {amount_str}\n"
                f"  🔹 *Posting Fee:* ${posting_fee:.2f}\n"
                f"  🔹 *Description*: {job_description}\n\n"
                f"Please respond with: *Yes* to confirm, *No* to cancel and return to the main menu\n"
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
            return await self.webhook_response(None, payloadResponse, None)

        except Exception as e:
            print(f"Error confirming job data: {e}")
            return {"error": "Failed to confirm job data"}

    async def post_job_data_save(self, parameters, recipient_number, chat_session_id):
        """
        Save the job data to the database and create a Stripe checkout session.

        Args:
            parameters (dict): The parameters from Dialogflow.
            recipient_number (str): The phone number of the recipient.
            chat_session_id (str): The chat session ID.

        Returns:
            dict: The webhook response after saving job data.
        """
        try:
            # Extract job details from parameters
            job_description = parameters.get("job_description", "N/A")
            job_category = parameters.get("job_category", "N/A")
            job_date = parameters.get("date", {})
            job_time = parameters.get("time", {})
            job_location = parameters.get("location_data", "N/A")
            amount = float(parameters.get('amount').get('amount'))
            posting_fee = float(parameters.get('posting_fee'))

            # Format job date and time
            job_date_str = f"{int(job_date.get('month'))}/{int(job_date.get('day'))}/{int(job_date.get('year'))}"
            job_time_obj = datetime.time(
                hour=int(job_time.get('hours', 0)),
                minute=int(job_time.get('minutes', 0)),
                second=int(job_time.get('seconds', 0))
            )
            job_time_str = job_time_obj.strftime("%I:%M %p")
            amount_str = f"${amount:.2f}" if amount else "N/A"

            # Combine date and time into a datetime object
            job_datetime = datetime.datetime(
                year=int(job_date.get('year')),
                month=int(job_date.get('month')),
                day=int(job_date.get('day')),
                hour=int(job_time.get('hours')),
                minute=int(job_time.get('minutes')),
                second=int(job_time.get('seconds'))
            )

            # Get or create job category
            category = await CategoryRepository.get_category_by_name(job_category)
            if not category:
                return {"error": f"Category '{job_category}' not found"}

            # Get user by phone number
            user = await UserRepository.get_user_by_phone_number(recipient_number)
            if not user:
                return {"error": "User not found"}

            # Create job entry in the database
            job = await JobRepository.create_job(
                job_description=job_description,
                category_id=category.id,
                date_time=job_datetime,
                amount=amount,
                posting_fee=posting_fee,
                zip_code=parameters.get("zip_code"),
                posted_by=user.id,
            )

            # Update chat session with job ID
            await ChatSessionRepository.update_chat_session_job_id(chat_session_id, job.id)

            # Format job ID
            job_id_padded = str(job.id).zfill(5)

            # Create or retrieve Stripe customer
            customer_data = {
                "name": user.name,
                "phone_number": user.phone_number
            }
            stripe_customer = await self.stripe_client.create_or_retrieve_customer(customer_data)
            if not stripe_customer:
                raise Exception('Failed to create or retrieve customer stripe.')

            # Create Stripe checkout session
            checkout_session_data = {
                'job_id': job_id_padded,
                'transaction_amount': amount,
                'job_category':job_category.capitalize(),
                'job_date':job_date_str,
                'job_time':job_time_str,
                'job_description': job_description,
                'posting_fee': posting_fee,
                'total_amount': (amount + posting_fee),
                'stripe_customer_id': stripe_customer.id,
                'recipient_number':recipient_number,
                'user_id':user.id
            }
            checkout_session = await self.stripe_client.create_checkout_session(checkout_session_data)
            if not checkout_session:
                raise Exception('Failed to create checkout sessions stripe.')

            # Update job with payment details
            update_job_data = {
                'payment_id': checkout_session.id,
                'payment_intent': checkout_session.payment_intent,
            }

            where_criteria = {"id": job.id}

            await JobRepository.update_job(where_criteria, update_job_data)

            # Create a response message
            response_message = (
                f"🎉 *Your job has been posted successfully!* 🎉\n\n"
                f"  🔹 *Job ID*: #{job_id_padded}\n"
                f"  🔹 *Job Category:* {job_category.capitalize()}\n"
                f"  🔹 *Date:* {job_date_str}\n"
                f"  🔹 *Time:* {job_time_str}\n"
                f"  🔹 *Location:* {job_location}\n"
                f"  🔹 *Amount:* {amount_str}\n"
                f"  🔹 *Posting Fee:* ${posting_fee:.2f}\n"
                f"  🔹 *Description*: {job_description}\n\n"
                f"Please proceed with the escrow payment to complete the posting.\n\n"
                f"*Note:* The address entered in Stripe will be used as the job location address.\n"
            )

            # Create payload response with a button for payment
            payload_response = {
                "richContent": [
                    {
                        "text": response_message
                    },
                    {
                        "type": "chips",
                        "options": [
                            {
                                "text": "Escrow Payment",
                                "anchor": {
                                    "href": checkout_session.url
                                }
                            }
                        ]
                    }
                ]
            }

            return await self.webhook_response(None, payload_response, None)

        except Exception as e:
            print(f"Error saving job data: {e}")
            return {"error": "Failed to save job data"}

    async def get_job_category(self, text):
        """
        Get the job category from the text using an Classification model API.

        Args:
            text (str): The text to extract the category from.

        Returns:
            str: The extracted job category.
        """

        return 'pet care' #testing
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {CLASSIFICATION_MODEL_API_KEY}'
        }
        payload = {
            'text': text
        }

        try:
            response = requests.post(CLASSIFICATION_MODEL_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            category = response.json().get('category')
            if category:
                return category
            else:
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error calling ML model API: {e}")
            return None

    async def is_valid_zip_code(self, zip_code):
        """
        Validate the zip code using Google Maps API and return the corresponding city and state.

        Args:
            zip_code (str): The zip code to validate.

        Returns:
            tuple: A tuple containing a boolean indicating validity and a dictionary with city and state information.
        """
        try:
            
            url = f"https://maps.googleapis.com/maps/api/geocode/json?address={zip_code}&key={self.api_key}&sensor=true"
            response = await sync_to_async(requests.get)(url)
            response.raise_for_status()
            data = response.json()

            if data['status'] == 'OK':
                results = data['results'][0]
                address_components = results['address_components']

                city = None
                state = None

                for component in address_components:
                    if 'locality' in component['types']:
                        city = component['long_name']
                    if 'administrative_area_level_1' in component['types']:
                        state = component['short_name']

                if city and state:
                    return True, {"city": city, "state_id": state}
                else:
                    return False, {}
            else:
                return False, {}
        except requests.RequestException as e:
            print(f"Error validating zip code: {e}")
            return False, {}
