import os
from flask import Flask, jsonify, request, render_template
from controllers.whatsapp_controller import WhatsAppController
from controllers.dialogflow_controller import DialogflowController
from config import VERIFY_TOKEN

app = Flask(__name__, static_folder='assets')

# Instantiate WhatsApp controller and Dialogflow controller
whatsapp_controller = WhatsAppController()
dialogflow_controller = DialogflowController()

# In-memory store for processed message IDs
processed_message_ids = set()

@app.route("/", methods=["GET"])
def home():
    """
    Home route to load the static HTML page.
    """
    return render_template("index.html")

@app.route("/webhook", methods=["POST", "GET"])
def webhook():
    """
    Webhook endpoint for WhatsApp.

    GET: Handles webhook verification.
    POST: Processes incoming messages and statuses.
    """
    if request.method == "GET":
        # Parse params from the webhook verification request
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        # Check if a token and mode were sent
        if mode and token:
            # Check the mode and token sent are correct
            if mode == "subscribe" and token == VERIFY_TOKEN:
                print("WEBHOOK_VERIFIED")
                return challenge, 200
            else:
                print("VERIFICATION_FAILED")
                return jsonify({"status": "error", "message": "Verification failed"}), 403
        else:
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
                            message_id = value["messages"][0]["id"]
                            if message_id in processed_message_ids:
                                print(f"Message {message_id} already processed.")
                                return jsonify({"status": "ok"}), 200

                            processed_message_ids.add(message_id)
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
            print(f"Error processing request: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/dialogflow_webhook", methods=["POST"])
def dialogflow_webhook():
    """
    Webhook endpoint for Dialogflow.

    POST: Processes incoming webhook requests from Dialogflow.
    """
    body = request.get_json()
    try:
        response = dialogflow_controller.handle_dialogflow_webhook(body)
        return jsonify(response), 200
    except Exception as e:
        print(f"Error processing Dialogflow webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=True)
