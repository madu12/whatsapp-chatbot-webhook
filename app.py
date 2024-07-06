from fastapi import FastAPI, Request, HTTPException
import os
from dotenv import load_dotenv
from pydantic import BaseModel
import logging

# Load environment variables from .env file (for local development)
load_dotenv()

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use environment variable for verification token
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

class WebhookRequest(BaseModel):
    object: str
    entry: list

@app.get("/")
def read_root():
    return {"message": "WhatsApp Webhook API is running"}

@app.get("/webhook")
async def verify_token(hub_mode: str, hub_challenge: str, hub_verify_token: str):
    logger.info(f"Verification request received: hub_mode={hub_mode}, hub_verify_token={hub_verify_token}")
    if hub_verify_token == VERIFY_TOKEN and hub_mode == "subscribe":
        return hub_challenge
    raise HTTPException(status_code=400, detail="Invalid verification token")

@app.post("/webhook")
async def handle_incoming_message(request: Request):
    try:
        data = await request.json()
        logger.info(f"Received message: {data}")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error processing incoming message: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
