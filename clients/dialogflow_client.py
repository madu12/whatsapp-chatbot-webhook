import json
from google.cloud import dialogflowcx_v3 as dialogflow
from google.oauth2 import service_account
from config import DIALOGFLOW_CX_CREDENTIALS, DIALOGFLOW_CX_AGENTID, DIALOGFLOW_CX_LOCATION

class DialogflowClient:
    def __init__(self):
        """
        Initialize the DialogflowClient with the necessary credentials.
        """
        dialogflow_credentials = json.loads(DIALOGFLOW_CX_CREDENTIALS)
        self.dialogflow_project_id = dialogflow_credentials["project_id"]
        self.dialogflow_agent_id = DIALOGFLOW_CX_AGENTID
        self.dialogflow_location = DIALOGFLOW_CX_LOCATION

        # Create credentials from the service account info
        credentials = service_account.Credentials.from_service_account_info(dialogflow_credentials)
        client_options = {
            "api_endpoint": "dialogflow.googleapis.com",
        }

        # Create a Dialogflow SessionsClient
        self.client = dialogflow.SessionsClient(credentials=credentials, client_options=client_options)

    def detect_intent(self, sender_message, recipient_number, chat_session_id=None):
        """
        Detect the intent of a message using Dialogflow.

        Args:
            sender_message (str): The message sent by the user.
            recipient_number (str): The phone number of the recipient.
            chat_session_id (str, optional): The chat session ID. Defaults to None.

        Returns:
            google.cloud.dialogflowcx_v3.types.DetectIntentResponse: The response from Dialogflow.
        """
        try:
            if sender_message and recipient_number:
                # Construct the session path
                session_id = f"{recipient_number}{'&' + chat_session_id if chat_session_id else ''}"
                session_path = f"projects/{self.dialogflow_project_id}/locations/{self.dialogflow_location}/agents/{self.dialogflow_agent_id}/sessions/{session_id}"

                # Create the query input
                query_input = dialogflow.QueryInput(
                    text=dialogflow.TextInput(text=sender_message),
                    language_code="en",
                )

                # Create the detect intent request
                request = dialogflow.DetectIntentRequest(
                    session=session_path,
                    query_input=query_input,
                )

                # Detect the intent and return the result
                response = self.client.detect_intent(request=request)
                return response.query_result
            else:
                return None
        except Exception as e:
            print(f"Error detecting intent: {e}")
            return None
