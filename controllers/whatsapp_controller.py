from datetime import datetime, timezone
import logging
import uuid
from clients.whatsapp_client import WhatsAppClient
from controllers.dialogflow_controller import DialogflowController
from database.repositories import JobRepository, UserRepository, ChatSessionRepository, AddressRepository
from config import WEBSITE_URL

class WhatsAppController:
    def __init__(self):
        """
        Initialize the WhatsAppController with the necessary clients and data structures.
        """
        self.whatsapp_client = WhatsAppClient()
        self.dialogflow_controller = DialogflowController()
        self.sessions = {}
        self.processed_message_ids = set()
        self.website_url = WEBSITE_URL

    async def process_text_message(self, recipient_number, recipient_name, recipient_message):
        """
        Process the text message received from the user.

        Args:
            recipient_number (str): The phone number of the recipient.
            recipient_message (str): The message sent by the recipient.
        """
        try:
            post_job_phrases = ["post job", "post a job", "post new job", "post another job"]
            find_job_phrases = ["find job", "find a job", "find new job", "find another job"]
            mark_complete_phrases = ["complete job", "mark as complete", "mark job as complete", "job complete", "done with job"]

            user = await UserRepository.get_user_by_phone_number(recipient_number)
            if not user:
                if recipient_message.lower() == "agree" or recipient_message.lower() == "decline":
                    if recipient_message.lower() == "agree":
                        await self.register_new_user(recipient_number, recipient_name)
                        return
                
                    if recipient_message.lower() == "decline":
                        await self.send_decline_message(recipient_number)
                else:
                    await self.request_user_agreement(recipient_number)
                    return

            if recipient_message.lower() == "help":
                await self.send_help_message(recipient_number)
                return
            
            if recipient_message.lower() == "privacy":
                await self.send_privacy_message(recipient_number)
                return
            
            if recipient_message.lower() == "my jobs":
                await self.job_list(recipient_number)
                return
            
            if recipient_message.lower() == "hi":
                await self.welcome_msg(recipient_number, recipient_name)
                return
            
            if recipient_message.lower() == "delete account":
                await self.handle_delete_account_request(recipient_number)
                return
            
            if recipient_message.lower() == "confirm delete":
                await self.handle_confirm_delete(recipient_number)
                return

            if recipient_message.lower() in post_job_phrases + find_job_phrases + mark_complete_phrases:
                await self.handle_job_action(recipient_number, recipient_message, user, post_job_phrases, find_job_phrases, mark_complete_phrases)
            else:
                await self.handle_continued_conversation(recipient_number, recipient_message, user)
        except Exception as e:
            print(f"Error processing text message: {e}")
            await self.send_error_message(recipient_number)

    async def handle_job_action(self, recipient_number, recipient_message, user, post_job_phrases, find_job_phrases, mark_complete_phrases):
        """
        Handle the job-related actions (post job, find job, or mark job as complete).

        Args:
            recipient_number (str): The phone number of the recipient.
            recipient_message (str): The message sent by the recipient.
            user (User): The user object retrieved from the database.
            post_job_phrases (list): List of phrases indicating a post job action.
            find_job_phrases (list): List of phrases indicating a find job action.
            mark_complete_phrases (list): List of phrases indicating a mark job as complete action.
        """
        try:
            chat_session_id = str(uuid.uuid4())
            self.sessions[recipient_number] = chat_session_id

            if any(phrase in recipient_message.lower() for phrase in post_job_phrases):
                recipient_message = "Post Job"
                await ChatSessionRepository.create_chat_session(chat_session_id, recipient_message, user.id)
            elif any(phrase in recipient_message.lower() for phrase in find_job_phrases):
                recipient_message = "Find Job"
                await ChatSessionRepository.create_chat_session(chat_session_id, recipient_message, user.id)
            elif any(phrase in recipient_message.lower() for phrase in mark_complete_phrases):
                recipient_message = "Mark Job as Complete"
                await ChatSessionRepository.create_chat_session(chat_session_id, recipient_message, user.id)

            dialogflow_response = await self.dialogflow_controller.handle_message(recipient_message, recipient_number, chat_session_id)
            if dialogflow_response:
                await self.process_dialogflow_response(recipient_number, dialogflow_response)
            else:
                await self.send_default_options(recipient_number)
        except Exception as e:
            print(f"Error handling job action: {e}")
            await self.send_error_message(recipient_number)

    async def handle_continued_conversation(self, recipient_number, recipient_message, user):
        """
        Handle the continued conversation when the user sends a non-job-related message.

        Args:
            recipient_number (str): The phone number of the recipient.
            recipient_message (str): The message sent by the recipient.
            user (User): The user object retrieved from the database.
        """
        try:
            chat_session_id = self.sessions.get(recipient_number)
            if not chat_session_id:
                chat_session = await ChatSessionRepository.get_latest_chat_session_by_user(user.id)
                if chat_session:
                    chat_session_id = str(chat_session.id)
                    self.sessions[recipient_number] = chat_session_id
                else:
                    chat_session_id = str(uuid.uuid4())
                    self.sessions[recipient_number] = chat_session_id
                    chat_session = await ChatSessionRepository.create_chat_session(chat_session_id, "Post Job", user.id)

            dialogflow_response = await self.dialogflow_controller.handle_message(recipient_message, recipient_number, chat_session_id)
            if dialogflow_response:
                await self.process_dialogflow_response(recipient_number, dialogflow_response)
            else:
                await self.send_default_options(recipient_number)
        except Exception as e:
            print(f"Error handling continued conversation: {e}")
            await self.send_error_message(recipient_number)

    async def process_dialogflow_response(self, recipient_number, dialogflow_response):
        """
        Process the response from Dialogflow and send the appropriate message to the user.

        Args:
            recipient_number (str): The phone number of the recipient.
            dialogflow_response (dict): The response from Dialogflow.
        """
        try:
            # Check for an error in the Dialogflow response
            if "error" in dialogflow_response:
                response_message = "Something went wrong, please try again."
                await self.whatsapp_client.send_whatsapp_message(recipient_number, response_message, 'text')
            else:
                # Handle button response
                if 'replyBtnMessage' in dialogflow_response and dialogflow_response['replyBtnMessage'] is not None:
                    await self.whatsapp_client.send_whatsapp_message(recipient_number, dialogflow_response['replyBtnMessage'], 'interactive')
                
                # Handle list response
                elif 'replyListMessage' in dialogflow_response and dialogflow_response['replyListMessage'] is not None:
                    await self.whatsapp_client.send_whatsapp_message(recipient_number, dialogflow_response['replyListMessage'], 'interactive')

                # Handle simple text response
                elif 'simpleTextMessage' in dialogflow_response and dialogflow_response['simpleTextMessage'] is not None:
                    await self.whatsapp_client.send_whatsapp_message(recipient_number, dialogflow_response['simpleTextMessage'], 'text')

                # Handle default options if no recognizable response
                else:
                    await self.send_default_options(recipient_number)

        except Exception as e:
            print(f"Error processing Dialogflow response: {e}")
            await self.send_error_message(recipient_number)

    async def send_default_options(self, recipient_number):
        """
        Send the default options (Post Job or Find Job) to the user.

        Args:
            recipient_number (str): The phone number of the recipient.
        """
        try:
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
                },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "Mark Job as Complete",
                            "title": "Mark Job as Complete"
                        }
                    }
            ]
            response_message = (
                f"*We encountered an issue processing your request.*\n\n"
                f"Please try one of the following options:\n"
                f'1️⃣ Post Job: Type "Post Job" to start posting a new job.\n'
                f'2️⃣ Find Job: Type "Find Job" to search for available jobs.\n'
                f'3️⃣ Mark Job as Complete: Type "Mark Job as Complete" to update the job status to complete.\n\n'
                f"If you need any assistance, just type 'help'. 💬"
            )
            interactive_message = await self.dialogflow_controller.create_button_message(response_message, buttons)
            await self.whatsapp_client.send_whatsapp_message(recipient_number, interactive_message, 'interactive')
        except Exception as e:
            print(f"Error sending default options: {e}")
            await self.send_error_message(recipient_number)

    async def handle_whatsapp_message(self, body):
        """
        Handle the incoming message from WhatsApp.

        Args:
            body (dict): The request body from WhatsApp.

        Returns:
            dict: The response to be sent back to WhatsApp.
        """
        try:
            value = body["entry"][0]["changes"][0]["value"]
            message = value["messages"][0]
            recipient_number = value["contacts"][0]["wa_id"]
            recipient_name = value["contacts"][0]["profile"]['name']
            message_id = message["id"]

            user = await UserRepository.get_user_by_phone_number(recipient_number)
            if not user:
                if message["type"] == "text":
                    recipient_message = message["text"]["body"]
                elif message["type"] == "interactive":
                    interactive_type = message['interactive']['type']
                    if interactive_type == 'button_reply':
                        recipient_message = message["interactive"]["button_reply"]["id"]
                    elif interactive_type == 'list_reply':
                        recipient_message = message["interactive"]["list_reply"]["id"]
                    else:
                        recipient_message = None

                if recipient_message:       
                    if recipient_message.lower() == "agree" or recipient_message.lower() == "decline":
                        if recipient_message.lower() == "agree":
                            await self.register_new_user(recipient_number, recipient_name)
                            return {"status": "ok"}
                    
                        if recipient_message.lower() == "decline":
                            await self.send_decline_message(recipient_number)
                            return {"status": "ok"}
                    else:
                        await self.request_user_agreement(recipient_number)
                        return {"status": "ok"}

            if message_id in self.processed_message_ids:
                return {"status": "ok"}

            self.processed_message_ids.add(message_id)

            if message["type"] == "text":
                recipient_message = message["text"]["body"]
                await self.process_text_message(recipient_number, recipient_name, recipient_message)
            elif message["type"] == "interactive":
                interactive_type = message['interactive']['type']

                # If the message is a button reply
                if interactive_type == 'button_reply':
                    interactive_message = message["interactive"]["button_reply"]["id"]
                    await self.process_text_message(recipient_number, recipient_name, interactive_message)
                elif interactive_type == 'list_reply':
                    interactive_message = message["interactive"]["list_reply"]["id"]
                    await self.process_text_message(recipient_number, recipient_name, interactive_message)
            else:
                response_message = 'This chatbot only supports text and interactive messages.'
                await self.whatsapp_client.send_whatsapp_message(recipient_number, response_message, 'text')

            return {"status": "ok"}
        except Exception as e:
            response_message = e
            await self.whatsapp_client.send_whatsapp_message(recipient_number, response_message, 'text')
            print(f"Error handling WhatsApp message: {e}")
            return {"status": "error", "message": str(e)}

    async def welcome_msg(self, recipient_number, recipient_name):
        """
        Send a welcome message.

        Args:
            recipient_number (str): The phone number of the recipient.
            recipient_name (str): The name of the recipient.
        """
        try:
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
                },
                {
                    "type": "reply",
                    "reply": {
                        "id": "Mark Job as Complete",
                        "title": "Mark Job as Complete"
                    }
                }
            ]
            response_message = (
                f"Hello, {recipient_name}! This is HOME SERVICE CHATBOT! 🏠🤖\n\n"
                f"✨ What would you like to do today?\n"
                f"1️⃣ Post Job\n"
                f"2️⃣ Find Job\n"
                f"3️⃣ Mark Job as Complete\n\n"
                f"If you need any assistance, just type 'help'. 💬"
            )
            interactive_message = await self.dialogflow_controller.create_button_message(response_message, buttons)
            await self.whatsapp_client.send_whatsapp_message(recipient_number, interactive_message, 'interactive')
        except Exception as e:
            print(f"Error welcome msg: {e}")
            await self.send_error_message(recipient_number)
            
    async def register_new_user(self, recipient_number, recipient_name):
        """
        Register a new user and send a welcome message.

        Args:
            recipient_number (str): The phone number of the recipient.
            recipient_name (str): The name of the recipient.
        """
        try:
            user = await UserRepository.create_user(recipient_name, recipient_number)
            if user:
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
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "Mark Job as Complete",
                            "title": "Mark Job as Complete"
                        }
                    }
                ]
                response_message = (
                    f"Hello, this is HOME SERVICE CHATBOT! 🏠🤖\n\n"
                    f"Welcome, {recipient_name}! You have been successfully registered in our system. 🎉\n\n"
                    f"✨ What would you like to do next?\n"
                    f"1️⃣ Post Job\n"
                    f"2️⃣ Find Job\n"
                    f"3️⃣ Mark Job as Complete\n\n"
                    f"If you need any assistance, just type 'help'. 💬"
                )
                interactive_message = await self.dialogflow_controller.create_button_message(response_message, buttons)
                await self.whatsapp_client.send_whatsapp_message(recipient_number, interactive_message, 'interactive')
        except Exception as e:
            print(f"Error registering new user: {e}")
            await self.send_error_message(recipient_number)
    
    async def request_user_agreement(self, recipient_number):
        """
        Request user consent for data handling before registration.

        Args:
            recipient_number (str): The phone number of the recipient.
            recipient_name (str): The name of the recipient.
        """
        try:
            buttons = [
                {
                    "type": "reply",
                    "reply": {
                        "id": "Agree",
                        "title": "Agree"
                    }
                },
                {
                    "type": "reply",
                    "reply": {
                        "id": "Decline",
                        "title": "Decline"
                    }
                }
            ]
            response_message = (
                f"Hello, this is HOME SERVICE CHATBOT! 🏠🤖\n\n"
                f"To proceed, please note that by using this service, your phone number will be saved for job-related notifications and updates."
                f"Your data is secure and handled according to our privacy policy. 🛡️ Reply 'Agree' to continue."
            )
            interactive_message = await self.dialogflow_controller.create_button_message(response_message, buttons)
            await self.whatsapp_client.send_whatsapp_message(recipient_number, interactive_message, 'interactive')
        except Exception as e:
            print(f"Error requesting user agreement: {e}")
            await self.send_error_message(recipient_number)


    async def send_decline_message(self, recipient_number):
        """
        Send a message to the user when they decline the privacy policy.

        Args:
            recipient_number (str): The phone number of the recipient.
        """
        try:
            user = await UserRepository.get_user_by_phone_number(recipient_number)
            if not user:
                decline_message = (
                    f"We respect your choice. However, you need to agree to our data handling policy to use our services. "
                    f"If you change your mind, please type 'Agree' to proceed."
                )
                await self.whatsapp_client.send_whatsapp_message(recipient_number, decline_message, 'text')
        except Exception as e:
            print(f"Error sending decline message: {e}")
            await self.send_error_message(recipient_number)

    async def send_help_message(self, recipient_number):
        """
        Send a help message to the user.

        Args:
            recipient_number (str): The phone number of the recipient.
        """
        try:
            help_message = (
                "📋 *Help Guide*\n\n"
                "   🔹 *Post Job:* Type 'Post Job' to start posting a new job.\n\n"
                "   🔹 *Find Job:* Type 'Find Job' to search for available jobs.\n\n"
                "   🔹 *My Jobs:* Type 'My Jobs' to see a list of jobs you have posted or accepted.\n\n"
                "   🔹 *Privacy:* Your data is secure. Type 'Privacy' for info.\n"

            )
            await self.whatsapp_client.send_whatsapp_message(recipient_number, help_message, 'text')
        except Exception as e:
            print(f"Error sending help message: {e}")
            await self.send_error_message(recipient_number)
    
    async def send_privacy_message(self, recipient_number):
        """
        Send a privacy policy message to the user.

        Args:
            recipient_number (str): The phone number of the recipient.
        """
        try:
            privacy_message = (
                "🔒 *Privacy Policy Overview*\n\n"
                "We take your privacy seriously. Your phone number and data are stored securely and used only for service-related communications, such as job notifications and updates. We do not share your data with unauthorized third parties.\n\n"
                "If you wish to delete your account and all associated data, please type 'Delete Account'.\n\n"
                f"For more details, please visit our full privacy policy at: {self.website_url}/privacy-policy"
            )
            await self.whatsapp_client.send_whatsapp_message(recipient_number, privacy_message, 'text')
        except Exception as e:
            print(f"Error sending privacy message: {e}")
            await self.send_error_message(recipient_number)


    async def send_error_message(self, recipient_number):
        """
        Send an error message to the user.

        Args:
            recipient_number (str): The phone number of the recipient.
        """
        try:
            response_message = "We encountered an issue processing your request. Please try again later."
            await self.whatsapp_client.send_whatsapp_message(recipient_number, response_message, 'text')
        except Exception as e:
            print(f"Error sending error message: {e}")

    async def notify_payment_success(self, session, customer_address):
        """
        Notify the user about the successful payment via WhatsApp.

        Args:
            session (object): The payment session object containing metadata.
            customer_address (object): The customer's address object.
        """
        try:
            address = (
                f"{customer_address.line1 if customer_address.line1 else ''} "
                f"{customer_address.line2 if customer_address.line2 else ''}, "
                f"{customer_address.city if customer_address.city else ''}, "
                f"{customer_address.state if customer_address.state else ''} "
                f"{customer_address.postal_code if customer_address.postal_code else ''}"
            ).strip()
            
            response_message = (
                f"🎉 *Your payment was successful!* 🎉\n\n"
                f"  🔹 *Job ID*: #{session.metadata.job_id}\n"
                f"  🔹 *Job Category:* {session.metadata.job_category}\n"
                f"  🔹 *Job Date & Time:* {session.metadata.job_date} @ {session.metadata.job_time}\n"
                f"  🔹 *Location:* {address}\n"
                f"  🔹 *Escrow Amount:* {session.metadata.job_amount}\n"
                f"  🔹 *Job Description*: {session.metadata.job_description}\n\n"
                f"Please proceed with the escrow payment to complete the posting.\n\n"
                f"*Note:* The address entered in Stripe will be used as the job location address.\n\n"
                f"What would you like to do next? 😊"
            )

            buttons = [
                {
                    "type": "reply",
                    "reply": {
                        "id": "Post Another Job",
                        "title": "Post Another Job"
                    }
                },
                {
                    "type": "reply",
                    "reply": {
                        "id": "Find Another Job",
                        "title": "Find Another Job"
                    }
                },
                {
                    "type": "reply",
                    "reply": {
                        "id": "Mark Job as Complete",
                        "title": "Mark Job as Complete"
                    }
                }
            ]
            interactive_message = await self.dialogflow_controller.create_button_message(response_message, buttons)
            await self.whatsapp_client.send_whatsapp_message(session.metadata.recipient_number, interactive_message, 'interactive')
        except Exception as e:
            print(f"Error generating payment success message: {e}")

    async def job_list(self, recipient_number):
        """
        Send a message listing the jobs posted or accepted by the user.

        Args:
            recipient_number (str): The phone number of the recipient.
        """
        try:
            # Fetch the user based on their phone number
            user = await UserRepository.get_user_by_phone_number(recipient_number)
            if user:
                order = [("id", "asc")]
                
                # Fetch jobs posted by the user
                posted_jobs = await JobRepository.find_all_jobs_with_conditions({
                    "posted_by": user.id
                }, order, 10)

                # Fetch jobs accepted by the user
                accepted_jobs = await JobRepository.find_all_jobs_with_conditions({
                    "accepted_by": user.id
                }, order, 10)

                # Construct the response message
                response_message = (
                    f"✨ *Here are your jobs:* ✨\n\n"
                )

                # Check and list posted jobs
                if posted_jobs:
                    response_message += "🌟 *Your Posted Jobs:*\n\n"
                    for idx, job in enumerate(posted_jobs, 1):
                        job_time_str = job.date_time.strftime("%m/%d/%Y at %I:%M %p")
                        response_message += (
                            f"*{idx}) Job ID #{job.id}:* {job.category.name.capitalize()} on {job_time_str} in ZIP {job.zip_code} for ${job.amount:.2f} - {job.status.capitalize()}\n\n"
                        )

                # Check and list accepted jobs
                if accepted_jobs:
                    response_message += "👍 *Your Accepted Jobs:*\n\n"
                    for idx, job in enumerate(accepted_jobs, 1):
                        job_time_str = job.date_time.strftime("%m/%d/%Y at %I:%M %p")
                        response_message += (
                            f"*{idx}) Job ID #{job.id}:* {job.category.name.capitalize()} on {job_time_str} in ZIP {job.zip_code} for ${job.amount:.2f} - {job.status.capitalize()}\n\n"
                        )

                # If no jobs were found, provide a different response
                if not posted_jobs and not accepted_jobs:
                    response_message = "🚫 You have no jobs posted or accepted."

                # Send the response via WhatsApp
                await self.whatsapp_client.send_whatsapp_message(recipient_number, response_message, 'text')
            else:
                await self.whatsapp_client.send_whatsapp_message(recipient_number, "User not found.", 'text')

        except Exception as e:
            print(f"Error finding jobs for user: {e}")
            await self.send_error_message(recipient_number)

    async def handle_delete_account_request(self, recipient_number):
        """
        Handle the user's request to delete their account.

        Args:
            recipient_number (str): The phone number of the recipient.
        """
        try:
            # Verify if the user exists in the database
            user = await UserRepository.get_user_by_phone_number(recipient_number)
            if not user:
                await self.whatsapp_client.send_whatsapp_message(
                    recipient_number,
                    "Your account could not be found. If you believe this is an error, please contact support.",
                    "text"
                )
                return
            
            # Send acknowledgment and ask for confirmation
            buttons = [
                {"type": "reply", "reply": {"id": "Confirm Delete", "title": "Confirm Delete"}},
                {"type": "reply", "reply": {"id": "Cancel", "title": "Cancel"}}
            ]
            response_message = (
                "⚠️ *Account Deletion Request*\n\n"
                "You have requested to delete your account. This action is irreversible. All your data, "
                "including posted jobs, accepted jobs, and payment details, will be permanently deleted.\n\n"
                "If you wish to proceed, please confirm by clicking 'Confirm Delete' below."
            )
            interactive_message = await self.dialogflow_controller.create_button_message(response_message, buttons)
            await self.whatsapp_client.send_whatsapp_message(recipient_number, interactive_message, "interactive")
        except Exception as e:
            logging.error(f"Error handling delete account request for {recipient_number}: {e}")
            await self.send_error_message(recipient_number)

    async def handle_confirm_delete(self, recipient_number):
        """
        Handle the user's request to delete their account under CCPA and GDPR compliance.

        Args:
            recipient_number (str): The phone number of the recipient.
        """
        try:
            # Verify the user exists
            user = await UserRepository.get_user_by_phone_number(recipient_number)
            if not user:
                await self.whatsapp_client.send_whatsapp_message(
                    recipient_number,
                    "Your account could not be found. Please contact support if you believe this is an error.",
                    "text"
                )
                return

            # Notify the user that the deletion process has started
            progress_message = (
                "🚨 *Account Deletion in Progress* 🚨\n\n"
                "We have received your request to delete your account. This process may take a few moments.\n\n"
                "⚙️ What’s happening:\n"
                "1️⃣ Anonymizing your information.\n"
                "2️⃣ Notifying impacted users.\n"
                "3️⃣ Finalizing the process.\n\n"
                "✨ *You will receive a confirmation shortly!* ✨"
            )
            await self.whatsapp_client.send_whatsapp_message(
                recipient_number,
                progress_message,
                "text"
            )

            # Perform the deletion steps
            deletion_success = True
            try:
                await self.anonymize_user_data(user)
                await self.notify_affected_users(user)
                await self.log_deletion_request(user)
            except Exception as deletion_error:
                deletion_success = False
                logging.error(f"Error during account deletion for user {user.id}: {deletion_error}")

            # Confirm deletion completion only if all steps succeeded
            if deletion_success:
                completion_message = (
                    "✅ *Account Deletion Completed* ✅\n\n"
                    "Your account and all associated data have been successfully deleted. Thank you for being a part of our journey! 🌟\n\n"
                    "💬 *We’re always here to help if you decide to return.* Feel free to reach out anytime.\n\n"
                )
                await self.whatsapp_client.send_whatsapp_message(
                    recipient_number,
                    completion_message,
                    "text"
                )
            else:
                error_message = (
                    "⚠️ An error occurred while processing your deletion request. "
                    "Please contact support for assistance. 🛡️"
                )
                await self.whatsapp_client.send_whatsapp_message(
                    recipient_number,
                    error_message,
                    "text"
                )

        except Exception as e:
            logging.error(f"Error handling confirm delete for recipient {recipient_number}: {e}")
            await self.whatsapp_client.send_whatsapp_message(
                recipient_number,
                "⚠️ An unexpected error occurred. Please contact support for assistance.",
                "text"
            )

    async def anonymize_user_data(self, user):
        """
        Anonymize user and related data for compliance.

        Args:
            user (User): The user object to anonymize.
        """
        try:
            # Step 1: Anonymize user record
            await UserRepository.update_user(
                user_id=user.id,
                update_data={
                    "name": "Deleted User",
                    "phone_number": None,
                    "deleted_at": datetime.now(timezone.utc),
                }
            )

            # Step 2: Anonymize user addresses
            await AddressRepository.update_address(
                where_criteria={"user_id": user.id},
                update_data={
                    "street": 'Deleted Address',
                    "city": "Deleted City",
                    "state": "XX",
                    "zip_code": "00000",
                    "is_active": "false"
                }
            )

            # Step 3: Soft delete chat sessions
            await ChatSessionRepository.update_chat_sessions(
                where_criteria={"user_id": user.id},
                update_data={"deleted_at": datetime.now(timezone.utc)}
            )

            # Step 4: Handle jobs posted by the user
            posted_jobs = await JobRepository.find_all_jobs_with_conditions(
                conditions={"posted_by": user.id},
                order=[("id", "asc")]
            )
            for job in posted_jobs:
                if job.status in ["pending", "posted", "accepted"]:
                    await JobRepository.update_job(
                        where={"id": job.id},
                        update_data={"status": "deleted", "deleted_at": datetime.now(timezone.utc)}
                    )

            # Step 5: Handle jobs accepted by the user
            accepted_jobs = await JobRepository.find_all_jobs_with_conditions(
                conditions={"accepted_by": user.id},
                order=[("id", "asc")]
            )
            for job in accepted_jobs:
                await JobRepository.update_job(
                    where={"id": job.id},
                    update_data={"accepted_by": None, "status": "pending"}
                )
        except Exception as e:
            logging.error(f"Error anonymizing user data: {e}")
            raise e

    async def notify_affected_users(self, user):
        """
        Notify users affected by the account deletion.

        Args:
            user (User): The user object whose deletion affects other users.
        """
        try:
            # Step 1: Notify job seekers
            posted_jobs = await JobRepository.find_all_jobs_with_conditions(
                conditions={"posted_by": user.id},
                order=[("id", "asc")]
            )
            for job in posted_jobs:
                if job.accepted_by:
                    seeker = await UserRepository.get_user_by_id(job.accepted_by)
                    if seeker:
                        await self.whatsapp_client.send_whatsapp_message(
                            seeker.phone_number,
                            f"⚠️ The job ID #{job.id} has been canceled due to the poster's account deletion.",
                            "text"
                        )

            # Step 2: Notify job posters
            accepted_jobs = await JobRepository.find_all_jobs_with_conditions(
                conditions={"accepted_by": user.id},
                order=[("id", "asc")]
            )
            for job in accepted_jobs:
                poster = await UserRepository.get_user_by_id(job.posted_by)
                if poster:
                    await self.whatsapp_client.send_whatsapp_message(
                        poster.phone_number,
                        f"⚠️ The job ID #{job.id} has been marked as available due to the acceptor's account deletion.",
                        "text"
                    )
        except Exception as e:
            logging.error(f"Error notifying affected users: {e}")
            raise e

    async def log_deletion_request(self, user):
        """
        Log the account deletion request for audit purposes.

        Args:
            user (User): The user object being deleted.
        """
        try:
            logging.info(
                f"📝 User ID {user.id} ('{user.name}') account deletion processed successfully at {datetime.now(timezone.utc)}."
            )
        except Exception as e:
            logging.error(f"Error logging deletion request: {e}")
            raise e