from config import STRIPE_SECRET_KEY, WEBSITE_URL
import stripe

class StripeClient:
    def __init__(self):
        """
        Initialize the StripeClient with the necessary credentials.
        """
        self.website_url = WEBSITE_URL
        stripe.api_key = STRIPE_SECRET_KEY

    async def create_or_retrieve_customer(self, customer_data):
        """
        Create a new Stripe customer or retrieve an existing one based on the provided phone number.

        :param customer_data: Dictionary containing 'name' and 'phone_number' keys.
        :return: Stripe customer object.
        """
        try:
            # Query Stripe for existing customers with the given phone number
            query = f"phone:'{customer_data['phone_number']}'"
            customers =  stripe.Customer.search(query=query, limit=1)
            
            if customers['data']:
                # Return the first customer if found
                return customers['data'][0]

            # Create a new customer if none found
            new_customer = stripe.Customer.create(
                name=customer_data['name'],
                phone=customer_data['phone_number']
            )
            
            return new_customer
        except stripe.error.StripeError as e:
            print(f"Error stripe create or retrieve customer: {e.user_message}")
            raise e

    async def create_checkout_session(self, checkout_session_data):
        """
        Create a new Stripe checkout session for job payment.

        :param checkout_session_data: Dictionary containing checkout session details.
        :return: Stripe checkout session object.
        """
        try:
            # Create the checkout session
            checkout_session = stripe.checkout.Session.create(
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f"#{checkout_session_data['job_id']} - Job Payment, ${checkout_session_data['transaction_amount']} for {checkout_session_data['job_description']} and posting fee ${checkout_session_data['posting_fee']}.",
                        },
                        'unit_amount': round(checkout_session_data['total_amount'] * 100),
                    },
                    'quantity': 1,
                }],
                payment_intent_data={
                    'capture_method': 'manual',
                },
                customer=checkout_session_data['stripe_customer_id'],
                billing_address_collection='required',
                mode='payment',
                success_url=f"{self.website_url}/success?paymentID={{CHECKOUT_SESSION_ID}}",
                cancel_url=self.website_url,
                after_expiration={
                    'recovery': {
                        'enabled': True,
                    },
                },
                metadata={
                    'job_id': checkout_session_data['job_id'],
                    'job_description': checkout_session_data['job_description'],
                    'job_category': checkout_session_data['job_category'],
                    'job_date': checkout_session_data['job_date'],
                    'job_time': checkout_session_data['job_time'],
                    'job_amount': checkout_session_data['total_amount'],
                    'recipient_number': checkout_session_data['recipient_number'],
                    'user_id': checkout_session_data['user_id']
                }
            )

            return checkout_session
        except stripe.error.StripeError as e:
            print(f"Error stripe create checkout session: {e.user_message}")
            raise e
