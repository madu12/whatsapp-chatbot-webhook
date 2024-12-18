import os
import stripe
from database.repositories import JobRepository, AddressRepository
from flask import Flask, jsonify, request, render_template, redirect,url_for, make_response
from controllers.whatsapp_controller import WhatsAppController
from clients.whatsapp_client import WhatsAppClient
from controllers.dialogflow_controller import DialogflowController
from clients.stripe_client import StripeClient

from config import WHATSAPP_VERIFY_TOKEN,  STRIPE_SECRET_KEY

app = Flask(__name__, static_folder='assets')

stripe.api_key = STRIPE_SECRET_KEY

# Instantiate WhatsApp controller, WhatsApp client, Dialogflow controller
whatsapp_controller = WhatsAppController()
dialogflow_controller = DialogflowController()
whatsapp_client = WhatsAppClient()
stripe_client = StripeClient()

# In-memory store for processed message IDs
processed_message_ids = set()

@app.route("/", methods=["GET"])
async def home():
    """
    Home route to load the static HTML page.
    """
    return render_template("index.html")

@app.route("/webhook", methods=["POST", "GET"])
async def webhook():
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
            if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
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
                            response = await whatsapp_controller.handle_whatsapp_message(body)
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
async def dialogflow_webhook():
    """
    Webhook endpoint for Dialogflow.

    POST: Processes incoming webhook requests from Dialogflow.
    """
    body = request.get_json()
    try:
        response = await dialogflow_controller.handle_dialogflow_webhook(body)
        if response:
            return jsonify(response), 200
        else:
            return jsonify({"status": "error", "message": "No response generated."}), 500
    except Exception as e:
        print(f"Error processing Dialogflow webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/success', methods=['GET'])
async def order_success():
    payment_id = request.args.get('paymentID')
    if not payment_id:
        return redirect(url_for('home'))

    session = stripe.checkout.Session.retrieve(payment_id)
    customer_address = session.customer_details.address

    if session and customer_address:
        address_data = {
            "street": f"{customer_address.line1} {customer_address.line2 if customer_address.line2 else ''}",
            "city": customer_address.city,
            "zip_code": customer_address.postal_code,
            "state": customer_address.state,
            "country": customer_address.country
        }

        result = await AddressRepository.register_address(address_data, session.metadata.user_id)

        address_id = result['address_data'].id if result['address_data'] else None

        update_job_data = {
            'status': 'posted',
            'payment_status': 'authorized',
            'payment_intent': session.payment_intent,
            'address_id': address_id
        }
        where_criteria = {"id": int(session.metadata.job_id), "payment_status": 'unpaid'}

        job = await JobRepository.update_job(where_criteria, update_job_data)
        if job:
            await whatsapp_controller.notify_payment_success( session, customer_address)

        return render_template(
            'success.html',
            customer_address=customer_address,
            session=session
        )
    else:
        return redirect(url_for('home'))

@app.route("/docs/<path:filename>", methods=["GET"])
def documentation_file(filename):
    """
    Serve the documentation files.
    """
    return render_template(f"docs/{filename}")


@app.route("/docs", methods=["GET"])
def documentation_index():
    """
    Redirect to the index file of the documentation.
    """
    return render_template("docs/index.html")

@app.route("/connected-account-verify", methods=["GET"])
def connected_account_verify():
    """
    Endpoint to verify a connected account.

    :return: Redirect URL for the user.
    """
    account_id = request.args.get("accountID")
    if not account_id:
        return jsonify({"error": "Missing accountID"}), 400

    try:
        redirect_url = stripe_client.verify_connected_account(account_id)
        return redirect(redirect_url)
    except Exception as e:
        print(f"Error verifying connected account: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=True)
