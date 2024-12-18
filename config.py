import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load Dialogflow credentials and agent details
DIALOGFLOW_CX_CREDENTIALS = os.getenv("DIALOGFLOW_CX_CREDENTIALS_JSON")
# Ensure the JSON string is formatted correctly for usage
if DIALOGFLOW_CX_CREDENTIALS:
    DIALOGFLOW_CX_CREDENTIALS = DIALOGFLOW_CX_CREDENTIALS.replace('\n', '\\n')

DIALOGFLOW_CX_AGENTID = os.getenv("DIALOGFLOW_CX_AGENTID")
DIALOGFLOW_CX_LOCATION = os.getenv("DIALOGFLOW_CX_LOCATION")

# Load WhatsApp credentials
WHATSAPP_CHATBOT_PHONE_NUMBER = os.getenv("WHATSAPP_CHATBOT_PHONE_NUMBER")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")

# Set default language if not specified in the environment variables
LANGUAGE = os.getenv("LANGUAGE", "en-US")

# Load Stripe credentials
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
WEBSITE_URL = os.getenv("WEBSITE_URL")

# Load Google Map credentials
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Load Classification Model credentials
CLASSIFICATION_MODEL_API_URL = os.getenv("CLASSIFICATION_MODEL_API_URL")
CLASSIFICATION_MODEL_API_KEY = os.getenv("CLASSIFICATION_MODEL_API_KEY")

# Load Encryption Key
AES_KEY = os.getenv("AES_KEY")
AES_IV = os.getenv("AES_IV")

# Ensure critical environment variables are loaded
required_vars = [
    DIALOGFLOW_CX_CREDENTIALS,
    DIALOGFLOW_CX_AGENTID,
    DIALOGFLOW_CX_LOCATION,
    WHATSAPP_CHATBOT_PHONE_NUMBER,
    WHATSAPP_TOKEN,
    WHATSAPP_VERIFY_TOKEN,
    STRIPE_SECRET_KEY,
    WEBSITE_URL,
    GOOGLE_MAPS_API_KEY,
    AES_KEY,
    AES_IV,
    CLASSIFICATION_MODEL_API_URL,
    CLASSIFICATION_MODEL_API_KEY
]

missing_vars = [var for var, value in zip([
    "DIALOGFLOW_CX_CREDENTIALS",
    "DIALOGFLOW_CX_AGENTID",
    "DIALOGFLOW_CX_LOCATION",
    "WHATSAPP_TOKEN",
    "WHATSAPP_CHATBOT_PHONE_NUMBER",
    "WHATSAPP_VERIFY_TOKEN",
    "STRIPE_SECRET_KEY",
    "WEBSITE_URL",
    "GOOGLE_MAPS_API_KEY",
    "AES_KEY",
    "AES_IV",
    "CLASSIFICATION_MODEL_API_URL",
    "CLASSIFICATION_MODEL_API_KEY"
], required_vars) if not value]

if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")
