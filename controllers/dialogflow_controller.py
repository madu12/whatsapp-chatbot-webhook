from clients.dialogflow_client import DialogflowClient
import datetime
from database.repositories import AddressRepository, ChatSessionRepository, JobRepository, CategoryRepository, UserRepository
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
            reply_list_message = None
            simple_text_message = None

            # Extract payload messages (for buttons and lists)
            payload_messages = [message for message in fulfillment_messages if hasattr(message, 'payload') and message.payload is not None]
            text_messages = [message for message in fulfillment_messages if 'text' in message.text]

            # Process payload messages for buttons and lists
            if payload_messages:
                buttons, lists, payload_text = await self.process_payload_messages(payload_messages)

                if not text_messages:
                    payload_text_message = payload_text
                else:
                    payload_text_message = text_messages[0].text.text[0]

                # Create button message if buttons are found
                if buttons:
                    reply_btn_message = await self.create_button_message(payload_text_message, buttons)

                # Create list message if lists are found
                if lists:
                    reply_list_message = await self.create_list_message(payload_text_message, lists)

            # Process simple text messages if no buttons or lists
            if not reply_btn_message and not reply_list_message and text_messages:
                simple_text_message = text_messages[0].text.text[0] if text_messages else None

            # Return the structured message based on the type found
            return {
                "replyBtnMessage": reply_btn_message,
                "replyListMessage": reply_list_message,
                "simpleTextMessage": simple_text_message
            }
        except Exception as e:
            print(f"Error processing Dialogflow response: {e}")
            raise e

    async def process_payload_messages(self, payload_messages):
        """
        Process payload messages to extract buttons, lists, and text.

        Args:
            payload_messages (list): List of payload messages.

        Returns:
            tuple: A tuple containing buttons, lists, and payload text.
        """
        buttons = []
        lists = []
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
                        title = option['text']
                        anchorHref = option.get('anchor', {}).get('href', "")
                        id = option.get('id', {})
                        if id:
                            lists.append({
                                "id": id,
                                "title": title
                            })
                        else:
                            if anchorHref:
                                buttons.append({
                                    "type": "url",
                                    "url": anchorHref,
                                    "title": title
                                })
                            else:
                                buttons.append({
                                    "type": "reply",
                                    "reply": {
                                        "id": title,
                                        "title": title
                                    }
                                })

        return buttons, lists, payload_text

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
    
    async def create_list_message(self, text, lists):
        """
        Create a list message for WhatsApp interactive messages.

        Args:
            text (str): The text to display with the list.
            lists (list): The list of items.

        Returns:
            dict: The interactive list message.
        """
        return {
            "interactive": {
                "type": "list",
                "body": {"text": text},
                "action": {
                    "button": "Choose an option",
                    "sections": [
                        {
                            "rows": lists
                        }
                    ]
                }
            }
        }

    async def webhook_response(self, text_response=None, payload_response=None, parameters=None):
        """
        Generate a webhook response for Dialogflow.

        Args:
            text_response (str, optional): The text response to be sent back.
            payload_response (dict, optional): The payload response (interactive messages).
            parameters (dict, optional): The session parameters to include in the response.

        Returns:
            dict: The structured webhook response.
        """
        try:
            response = {
                "fulfillmentResponse": {
                    "messages": []
                },
                "sessionInfo": {
                    "parameters": {}
                }
            }

            # Add a text message to the response if provided
            if text_response:
                response["fulfillmentResponse"]["messages"].append(
                    {
                        "text": {
                            "text": [text_response]
                        }
                    }
                )

            # Add payload (interactive) messages to the response if provided
            if payload_response:
                response["fulfillmentResponse"]["messages"].append(
                    {
                        "payload": payload_response
                    }
                )

            # Include any session parameters if provided
            if parameters:
                response["sessionInfo"]["parameters"] = parameters

            # Clean up the response by removing empty keys
            if not response["sessionInfo"]["parameters"]:
                del response["sessionInfo"]
            if not response["fulfillmentResponse"]["messages"]:
                del response["fulfillmentResponse"]

            return response

        except Exception as e:
            print(f"Error generating webhook response: {e}")
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
                if tag == 'predictCategory':
                    webhook_response = await self.predict_category(parameters, text)
                    return webhook_response
                
                if tag == 'confirmCategory':
                    confirmed_category = parameters.get('job_category')
                    job_description = parameters.get('job_description')
                    webhook_response = await self.confirm_category(job_description, confirmed_category)
                    return webhook_response
                
                if tag == 'validateCollectedPostJobData' or tag == 'validateCollectedFindJobData':
                    webhook_response = await self.validate_job_data(parameters, text)
                    return webhook_response

                if tag == 'postJobDataConfirmation':
                    response = await self.post_job_data_confirmation(parameters)
                    return response

                if tag == 'postJobDataSave':
                    response = await self.post_job_data_save(parameters, recipient_number, chat_session_id)
                    return response
                
                if tag == 'findJobDataList':
                    response = await self.find_job_data_list(parameters)
                    return response
                
                if tag == 'foundJobsSelectedID':
                    response = await self.found_jobs_selected_id(parameters, recipient_number)
                    return response
                
                if tag == 'assignUserToAcceptedJob':
                    response = await self.assign_user_to_accepted_job(parameters, recipient_number)
                    return response
                
                

            return {"status": "error", "message": "No valid tag found in fulfillment info."}
        except Exception as e:
            print(f"Error processing Dialogflow webhook: {e}")
            return {"status": "error", "message": str(e)}
        
    async def predict_category(self, parameters, text=None):
        """
        Predict the job category using the ML model.

        Args:
            parameters (dict): The parameters from Dialogflow.

        Returns:
            dict: The webhook response with updated parameters.
        """
        try:
            json_parameters = {}

            # Combine existing job description with new text if provided
            if 'job_description' in parameters and parameters['job_description']:
                if text and text not in parameters['job_description'] and text not in ['Yes', 'No']:
                    json_parameters["job_description"] = f"{parameters['job_description']} {text}".strip()
                else:
                    json_parameters["job_description"] = parameters['job_description']
            else:
                json_parameters["job_description"] = text

            # Get job type (post_job/find_job)
            if 'job_type' in parameters and parameters['job_type']:
                json_parameters["job_type"] = parameters['job_type']

            # Call the ML model to get category suggestions
            ml_response = await self.get_job_category(json_parameters["job_description"])
            if ml_response:
                category = ml_response.get('category')
                suggested_by_gemini = ml_response.get('suggested_by_gemini')
                verification_status_by_gemini = ml_response.get('verification_status_by_gemini', 'incorrect').lower()

                # Normalize category and suggested_by_gemini to capitalize for display
                if category:
                    category = category.capitalize()
                if suggested_by_gemini:
                    suggested_by_gemini = suggested_by_gemini.capitalize()

                # Case 1: ML model returns one category or both categories are the same
                if category and (not suggested_by_gemini or category == suggested_by_gemini):
                    if(json_parameters["job_type"]):
                        if(json_parameters["job_type"] == 'post_job'):
                            response_message = (
                                f"We recommend posting your job under the *'{category}'* category. "
                                "Please confirm if this is correct."
                            )
                        
                        if(json_parameters["job_type"] == 'find_job'):
                            response_message = (
                                f"We recommend finding your job under the *'{category}'* category. "
                                "Please confirm if this is correct."
                            )

                        payload_response = {
                            "richContent": [
                                {
                                    "text": response_message
                                },
                                {
                                    "type": "chips",
                                    "options": [
                                        {"text": "Yes"},
                                        {"text": "No"}
                                    ]
                                }
                            ]
                        }
                        json_parameters["job_category"] = category
                        json_parameters["category_predicted"] = "single"
                        return await self.webhook_response(None, payload_response, json_parameters)

                # Case 2: Gemini verification suggests a different category and verification_status_by_gemini is incorrect
                elif verification_status_by_gemini == 'incorrect' and suggested_by_gemini and suggested_by_gemini != 'None':
                    
                    if(json_parameters["job_type"] != 'None'):
                        if(json_parameters["job_type"] == 'post_job'):
                            response_message = (
                                f"We recommend posting your job under the *'{suggested_by_gemini}'* category. "
                                "Please confirm if this is correct."
                            )
                        
                        if(json_parameters["job_type"] == 'find_job'):
                            response_message = (
                                f"We recommend finding your job under the *'{suggested_by_gemini}'* category. "
                                "Please confirm if this is correct."
                            )

                    payload_response = {
                        "richContent": [
                            {
                                "text": response_message
                            },
                            {
                                "type": "chips",
                                "options": [
                                    {"text": "Yes"},
                                    {"text": "No"}
                                ]
                            }
                        ]
                    }
                    json_parameters["job_category"] = suggested_by_gemini
                    json_parameters["category_predicted"] = "single"
                    return await self.webhook_response(None, payload_response, json_parameters)

                # Case 3: ML model returns multiple suggestions and verification_status_by_gemini is correct
                elif category and suggested_by_gemini and suggested_by_gemini != 'None' and verification_status_by_gemini == 'correct':
                    response_message = (
                        f"We have detected multiple categories for your job:\n"
                        f"🔹 {category}\n"
                        f"🔹 {suggested_by_gemini}\n\n"
                        "Please confirm the category you prefer."
                    )

                    payload_response = {
                        "richContent": [
                            {
                                "text": response_message
                            },
                            {
                                "type": "chips",
                                "options": [
                                    {"text": category},
                                    {"text": suggested_by_gemini},
                                ]
                            }
                        ]
                    }
                    json_parameters["category_predicted"] = "multiple"
                    return await self.webhook_response(None, payload_response, json_parameters)

                # Case 4: Gemini verification suggests 'none' as category
                elif verification_status_by_gemini == 'incorrect' and suggested_by_gemini == 'None':
                    json_parameters["category_predicted"] = "zero"
                    return await self.webhook_response(None, None, json_parameters)

                # Case 5: ML model cannot predict the category
                else:
                    json_parameters["category_predicted"] = "zero"
                    return await self.webhook_response(None, None, json_parameters)
        except Exception as e:
            print(f"Error processing job data: {e}")
            return {"message": "Error processing job data.", "status": 500}

    async def confirm_category(self, job_description, confirmed_category):
        """
        Confirm the job category with the ML model.

        Args:
            job_description (str): The job description.
            confirmed_category (str): The category confirmed by the user.

        Returns:
            dict: The response from the ML model.
        """
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {CLASSIFICATION_MODEL_API_KEY}'
        }
        payload = {
            'service_description': job_description,
            'confirmed_category': confirmed_category
        }

        try:
            response = await sync_to_async(requests.post)(f"{CLASSIFICATION_MODEL_API_URL}/confirm_category", json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error confirming category with ML model: {e}")
            return {"error": str(e)}
        
    async def validate_job_data(self, parameters, text=None):
        """
        Validate the collected post job data.

        Args:
            parameters (dict): The parameters from Dialogflow.

        Returns:
            dict: The webhook response with updated parameters.
        """
        try:
            json_parameters = {}

            # Update job description
            if 'job_description' in parameters and parameters['job_description']:
                if text and text not in parameters['job_description'] and text not in ['Yes', 'No']:
                    json_parameters["job_description"] = f"{parameters['job_description']} {text}".strip()
                else:
                    json_parameters["job_description"] = parameters['job_description']
            else:
                json_parameters["job_description"] = text

            # Extract date and time if not already set
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

            # Validate zip code
            if parameters.get('zip_code'):
                zip_code = parameters.get('zip_code')
                valid_zip_code, zip_code_data = await self.is_valid_zip_code(zip_code)
                if not valid_zip_code:
                    json_parameters["zip_code"] = None
                else:
                    json_parameters["location_data"] = f"{zip_code_data['city']}, {zip_code_data['state_id']}"

            # Validate amount
            if parameters.get('amount'):
                if float(parameters['amount']['amount']) < 10:
                    json_parameters["amount"] = None
                    return await self.webhook_response("Minimum price is $10 for this job.", None, json_parameters)
            
            return await self.webhook_response(None, None, json_parameters)

        except Exception as e:
            print(f"Error validating job data: {e}")
            return {"message": "Error validating job data.", "status": 500}

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

    async def find_job_data_list(self, parameters, error_text=None, json_parameters=None):
        """
        Search parameters for job finding.

        Args:
            parameters (dict): The parameters from Dialogflow.
            error_text (str, optional): Error text to display if needed.
            json_parameters (dict, optional): Additional JSON parameters to pass.

        Returns:
            dict: WhatsApp interactive list message content.
        """
        try:
            job_category = parameters.get("job_category", None)
            job_date = parameters.get("date", {})
            job_time = parameters.get("time", {})
            job_zip_code = parameters.get("zip_code", None)
            amount = parameters.get("amount", {})

            job_category_id = None

            # Get the category ID if a job category is provided
            if job_category:
                category = await CategoryRepository.get_category_by_name(job_category)
                if category:
                    job_category_id = category.id

            # Construct conditions
            conditions = {
                **({"category_id": job_category_id} if job_category_id else {}),
                **({"amount": {"gte": amount.get('amount')}} if amount and amount.get('amount') else {}),
                **({"zip_code": job_zip_code} if job_zip_code else {}),
                **({"status": "posted"}),
                **({"payment_status": "authorized"})
            }

            # Handle date and time filtering
            if job_date:
                year = int(job_date.get('year', 0))
                month = int(job_date.get('month', 0))
                day = int(job_date.get('day', 0))
                hour = int(job_time.get('hours', 0)) if job_time else 0
                minute = int(job_time.get('minutes', 0)) if job_time else 0
                second = int(job_time.get('seconds', 0)) if job_time else 0

                if year and month and day:  # Ensure year, month, and day are present
                    formatted_utc_date_time = datetime.datetime(
                        year=year,
                        month=month,
                        day=day,
                        hour=hour,
                        minute=minute,
                        second=second
                    )
                    conditions["date_time"] = {"gte": formatted_utc_date_time}

            # Sort order and limit
            order = [("amount", "desc"), ("date_time", "asc")]

            isFoundJobs = 'No'

            # Find jobs
            found_jobs = await JobRepository.find_all_jobs_with_conditions(conditions, order, limit=5)
            if found_jobs:
                isFoundJobs = 'Yes'
                if error_text:
                    summary_text = (
                        f"⚠️ {error_text} ⚠️\n\n"
                    )
                else:
                    summary_text = (
                        f"✨ *Here are the jobs matching your criteria:* ✨\n\n"
                    )
                # Dynamically create options for each job
                options = []
                for idx, job in enumerate(found_jobs, 1):
                    job_time_str = job.date_time.strftime("%m/%d/%Y @ %I:%M %p")
                    job_title =  f"Job #{str(job.id)}"
                    job_id = str(job.id)
                    options.append({"text": job_title, "id": job_id})
                    summary_text += (
                        f"*{idx}) Category: {job.category.name.capitalize()} - {job_time_str} in {job.zip_code} - ${job.amount:.2f} (Job #{job.id})*\n"
                        f"Job Requirement: {job.job_description}\n\n"
                    )
                summary_text += "Which job do you want to accept?"

                payload_response = {
                    "richContent": [
                        {
                            "text": summary_text
                        },
                        {
                            "type": "chips",
                            "options": options
                        }
                    ]
                }

                if not json_parameters:
                    json_parameters = {}
                json_parameters["is_found_jobs"] = isFoundJobs

                return await self.webhook_response(None, payload_response, json_parameters)

            else:
                summary_text = "Unfortunately, we currently do not have any jobs that match the criteria entered. Please adjust your criteria."
                if not json_parameters:
                    json_parameters = {}
                json_parameters["is_found_jobs"] = isFoundJobs
                return await self.webhook_response(summary_text, None, json_parameters)

        except Exception as e:
            print(f"Error finding job data: {e}")
            return {"error": "Failed to find job data"}

    async def found_jobs_selected_id(self, parameters, recipient_number):
        """
        Search parameters for job finding.

        Args:
            parameters (dict): The parameters from Dialogflow.
            recipient_number (str): The phone number of the recipient.

        Returns:
            dict: WhatsApp interactive list message content.
        """
        try:
            selected_job_id = parameters.get("selected_job_id", None)
            
            # Get the selected job by job ID
            selected_job = await JobRepository.find_job_with_conditions({"id": selected_job_id})
            if not selected_job:
                return await self.find_job_data_list(
                    parameters, 
                    error_text="*Invalid selection.*\n*Please choose a valid job from the list:*",
                    json_parameters={"selected_own_job_id": "No", "selected_same_time_job_id": "No", "selected_job_id_is_valid": "No"}
                )

            # Get user by phone number
            user = await UserRepository.get_user_by_phone_number(recipient_number)
            if not user:
                 print({"error": "User not found"})

            if selected_job.posted_by != user.id:
                # Check if the user already accepted jobs at the same time
                same_time_job_exist = await JobRepository.find_job_with_conditions({
                    "date_time": selected_job.date_time,
                    "accepted_by": user.id
                })

                if same_time_job_exist:
                    return await self.find_job_data_list(
                        parameters, 
                        error_text="*You already accepted jobs at the same time.*\n*Please choose a different job from the list:*",
                        json_parameters={"selected_own_job_id": "No", "selected_same_time_job_id": "Yes", "selected_job_id_is_valid": "Yes"}
                    )

                # Prepare the job details
                selected_job_date_str = selected_job.date_time.strftime("%m/%d/%Y")
                selected_job_time_str = selected_job.date_time.strftime("%I:%M %p")

                json_parameters = {
                    "selected_own_job_id": "No",
                    "selected_same_time_job_id": "No",
                    "selected_job_id_is_valid": "Yes"
                }

                # Create a response message
                response_message = (
                    f"✨ *Great! Please confirm you want to accept this job:* ✨\n\n"
                    f"  🔹 *Job Category:* {selected_job.category.name.capitalize()}\n"
                    f"  🔹 *Date:* {selected_job_date_str}\n"
                    f"  🔹 *Time:* {selected_job_time_str}\n"
                    f"  🔹 *Location:* {selected_job.zip_code}\n"
                    f"  🔹 *Amount:* ${selected_job.amount:.2f}\n"
                    f"  🔹 *Requirement:* {selected_job.job_description}\n\n"
                    f"Please respond with: *Accept* to confirm, *Decline* to cancel and return to the main menu\n"
                )

                payload_response = {
                    "richContent": [
                        {
                            "text": response_message
                        },
                        {
                            "type": "chips",
                            "options": [
                                {"text": "Accept"},
                                {"text": "Decline"}
                            ]
                        }
                    ]
                }
                return await self.webhook_response(None, payload_response, json_parameters)

            else:
                return await self.find_job_data_list(
                    parameters, 
                    error_text="*This is your job and you can't select it.*\n*Please choose a different job from the list:*",
                    json_parameters={"selected_own_job_id": "Yes", "selected_same_time_job_id": "No", "selected_job_id_is_valid": "Yes"}
                )

        except Exception as e:
            print(f"Error finding job data: {e}")
            return {"error": "Failed to find job data"}

    async def assign_user_to_accepted_job(self, parameters, recipient_number):
        """
        Assign a user to an accepted job based on the provided parameters.

        Args:
            parameters (dict): The parameters from Dialogflow.
            recipient_number (str): The phone number of the recipient.

        Returns:
            dict: WhatsApp interactive list message content.
        """
        try:
            selected_job_id = parameters.get("selected_job_id")
            
            # Get the selected job by job ID
            selected_job = await JobRepository.find_job_with_conditions({"id": selected_job_id})
            if not selected_job:
                return await self.find_job_data_list(
                    parameters,
                    error_text="*Invalid selection.*\n*Please choose a valid job from the list:*",
                    json_parameters={"selected_own_job_id": "No", "selected_same_time_job_id": "No", "selected_job_id_is_valid": "No"}
                )

            # Check if the job is already accepted or not in 'Posted' status
            if selected_job.accepted_by or selected_job.status.lower() != "posted":
                return await self.find_job_data_list(
                    parameters,
                    error_text="*This job is no longer available for acceptance. Please choose another job.*",
                    json_parameters={"selected_own_job_id": "No", "selected_same_time_job_id": "No", "selected_job_id_is_valid": "No"}
                )
            
            # Get user by phone number
            user = await UserRepository.get_user_by_phone_number(recipient_number)
            if not user:
                 print({"error": "User not found"})

            # Fetch the full address data from the Address table
            address = await AddressRepository.get_address_by_id(selected_job.address_id)
            if not address:
                print({"error": "Address not found"})

            # Update the job status to accepted
            update_job_data = {
                'status': 'accepted',
                'accepted_by': user.id
            }
            where_criteria = {"id": selected_job_id}
            await JobRepository.update_job(where_criteria, update_job_data)

            # Format the job details
            selected_job_date_str = selected_job.date_time.strftime("%m/%d/%Y")
            selected_job_time_str = selected_job.date_time.strftime("%I:%M %p")

            # Format the full address
            full_address = f"{address.street}, {address.city}, {address.state} {address.zip_code}"

            # Create the response message
            response_message = (
                f"✨ *Great! You've successfully accepted the job!* ✨\n\n"
                f"We'll see you at *{full_address}* on *{selected_job_date_str}* at *{selected_job_time_str}*.\n"
                f"You'll receive *${selected_job.amount:.2f}* after completing this job.\n\n"
                f"*Job Details:* {selected_job.job_description}\n"
            )

            return await self.webhook_response(response_message, None, None)

        except Exception as e:
            print(f"Error in assign user to accepted job: {e}")
            return {"error": "An error occurred while processing the job data."}

    async def get_job_category(self, service_description):
        """
        Predict the job category using the ML model.

        Args:
            job_description (str): The job description.

        Returns:
            dict: The response from the ML model with category suggestions.
        """

        # Phrases to be removed from the service description
        post_job_phrases = ["post job", "post a job", "post new job", "post another job"]
        find_job_phrases = ["find job", "find a job", "find new job", "find another job"]

        # Clean the service description by removing unwanted phrases
        for phrase in post_job_phrases + find_job_phrases:
            service_description = service_description.replace(phrase, "").strip()

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {CLASSIFICATION_MODEL_API_KEY}'
        }
        payload = {
            'service_description': service_description
        }

        try:
            response = await sync_to_async(requests.post)(f"{CLASSIFICATION_MODEL_API_URL}/predict", json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
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
