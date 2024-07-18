import json
from google.cloud import dialogflowcx_v3 as dialogflow
from google.oauth2 import service_account
from config import DIALOGFLOW_CX_CREDENTIALS, DIALOGFLOW_CX_AGENTID, DIALOGFLOW_CX_LOCATION

class DialogflowClient:
    def __init__(self):
        dialogflow_credentials = json.loads(DIALOGFLOW_CX_CREDENTIALS)
        self.dialogflow_project_id = dialogflow_credentials["project_id"]
        self.dialogflow_agent_id = DIALOGFLOW_CX_AGENTID
        self.dialogflow_location = DIALOGFLOW_CX_LOCATION

        credentials = service_account.Credentials.from_service_account_info(dialogflow_credentials)
        client_options = {
            "api_endpoint": "dialogflow.googleapis.com",
        }

        self.client = dialogflow.SessionsClient(credentials=credentials, client_options=client_options)

    def detect_intent(self, sender_message, recipient_number, chat_session_id=None):
        try:
            if sender_message and recipient_number:
                session_id = f"{recipient_number}{'&' + chat_session_id if chat_session_id else ''}"
                session_path = f"projects/{self.dialogflow_project_id}/locations/{self.dialogflow_location}/agents/{self.dialogflow_agent_id}/sessions/{session_id}"

                query_input = dialogflow.QueryInput(
                    text=dialogflow.TextInput(text=sender_message),
                    language_code="en",
                )

                request = dialogflow.DetectIntentRequest(
                    session=session_path,
                    query_input=query_input,
                )

                response = self.client.detect_intent(request=request)
                return response.query_result
            else:
                return None
        except Exception as e:
            print(f"Error detecting intent: {e}")
            return None
