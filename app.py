import os
import json
import logging
from flask import Flask, jsonify, request
from controllers.whatsapp_controller import WhatsAppController
from config import VERIFY_TOKEN

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Instantiate WhatsApp controller
whatsapp_controller = WhatsAppController()

# Required webhook verification for WhatsApp
@app.route("/", methods=["GET"])
def home():
    return "WhatsApp Webhook is listening!"

# Accepts POST and GET requests at /webhook endpoint
@app.route("/webhook", methods=["POST", "GET"])
def webhook():
    if request.method == "GET":
        # Parse params from the webhook verification request
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        # Check if a token and mode were sent
        if mode and token:
            # Check the mode and token sent are correct
            if mode == "subscribe" and token == VERIFY_TOKEN:
                # Respond with 200 OK and challenge token from the request
                print("WEBHOOK_VERIFIED")
                return challenge, 200
            else:
                # Responds with '403 Forbidden' if verify tokens do not match
                print("VERIFICATION_FAILED")
                return jsonify({"status": "error", "message": "Verification failed"}), 403
        else:
            # Responds with '400 Bad Request' if verify tokens do not match
            print("MISSING_PARAMETER")
            return jsonify({"status": "error", "message": "Missing parameters"}), 400

    elif request.method == "POST":
        body = request.get_json()
        try:
            if body.get("object"):
                entries = body.get("entry", [])
                for entry in entries:
                    changes = entry.get("changes", [])
                    for change in changes:
                        value = change.get("value", {})
                        if "messages" in value:
                            response = whatsapp_controller.handle_whatsapp_message(body)
                            return jsonify(response), 200
                        elif "statuses" in value:
                            # Handle statuses and return status details
                            statuses = value["statuses"]
                            status_messages = [status["status"] for status in statuses]
                            return jsonify({"status": "ok", "message": f"Received a status update: {', '.join(status_messages)}"}), 200
                return jsonify({"status": "error", "message": "Not a WhatsApp API event"}), 404
            else:
                return jsonify({"status": "error", "message": "Not a WhatsApp API event"}), 404
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))  # Ensure PORT environment variable is used if set
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=True)
