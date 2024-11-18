from config import STRIPE_SECRET_KEY, WEBSITE_URL
import stripe
from database.repositories import StripeUserRepository
from utils.general_utils import GeneralUtils

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

    async def create_connect_account(self):
        """
        Create a Stripe Connect Express Account.

        :return: Stripe Connect account object.
        """
        try:
            connect_account = stripe.Account.create(
                type='express',
                country='US',
                capabilities={
                    'transfers': {'requested': True},
                },
            )
            return connect_account
        except stripe.error.StripeError as e:
            print(f"Error in create_connect_account: {e.user_message}")
            raise e
        
    def create_connect_account_link(self, account_id):
        """
        Create a Stripe Connect Account link.

        :param account_id: Stripe account ID.
        :return: Account link URL.
        """
        try:
            utils = GeneralUtils()
            encrypted_account_id = utils.encrypt_aes_url_safe(account_id)
            account_link = stripe.AccountLink.create(
                account=account_id,
                refresh_url=f"{self.website_url}/connected-account-verify?accountID={encrypted_account_id}",
                return_url=f"{self.website_url}",
                type="account_onboarding"
            )
            return account_link
        except stripe.error.StripeError as e:
            print(f"Error creating Stripe Connect Account link: {e.user_message}")
            raise e

    def verify_connected_account(self, encrypted_account_id):
        """
        Verify and handle a Stripe Connect Account using the encrypted account ID.

        :param encrypted_account_id: Encrypted Stripe account ID.
        :return: Redirect URL for the user.
        """
        try:
            utils = GeneralUtils()
            stripe_user_id = utils.decrypt_aes_url_safe(encrypted_account_id)

            # Check if the account exists in the database
            existing_connect_account = StripeUserRepository.get_stripe_user_by_stripe_user_id(stripe_user_id)

            if existing_connect_account:
                # Create and return a new Connect Account onboarding link
                return self.create_connect_account_link(stripe_user_id)
            else:
                # Redirect to the website homepage or another fallback URL
                return self.website_url
        except Exception as e:
            print(f"Error verifying connected account: {e}")
            raise e
    
    async def get_connected_account(self, account_id):
        """
        Retrieve the Stripe Connected Account details.

        Args:
            account_id (str): Stripe account ID.

        Returns:
            dict: Stripe account details.
        """
        try:
            account = stripe.Account.retrieve(account_id)
            return account
        except Exception as e:
            print(f"Error retrieving connected account: {e}")
            raise e
        
    def create_login_link(self, account_id):
        """
        Create a Stripe Connect Login Link for the Express Dashboard.

        Args:
            account_id (str): Stripe account ID.

        Returns:
            dict: Login link object containing the URL.
        """
        try:
            login_link = stripe.Account.create_login_link(account_id)
            return login_link
        except Exception as e:
            print(f"Error creating login link: {e}")
            raise e
        
    async def capture_payment(self, payment_intent_id, amount, posting_fee, job_id):
        """
        Capture a payment from the job poster and create a top-up for the net amount to be paid to the job seeker.

        Args:
            payment_intent_id (str): The Payment Intent ID.
            amount (float): The total payment amount.
            posting_fee (float): The fee for posting the job.
            job_id (int): The job ID.

        Returns:
            dict: Captured payment details.
        """
        try:
            # Step 1: Calculate the total amount to capture and the net amount for the top-up
            amount_to_capture = int((amount + posting_fee) * 100)
            net_amount = int((amount - posting_fee) * 100)

            # Step 2: Capture the payment from the job poster
            captured_payment = stripe.PaymentIntent.capture(
                payment_intent_id,
                amount_to_capture=amount_to_capture
            )

            if captured_payment and captured_payment['status'] == 'succeeded':
                # Step 3: Create a top-up for the net amount to pay the job seeker
                top_up = stripe.Topup.create(
                    amount=net_amount,
                    currency='usd',
                    description=f"Top-up for #{str(job_id).zfill(5)} job payout",
                    statement_descriptor="Payout top-up"
                )
            return captured_payment
        
        except Exception as ex:
            # Log general exceptions
            print(f"An unexpected error occurred: {str(ex)}")
            raise ex

    async def create_payout(self, account_id, amount, posting_fee, job_id):
        """
        Create a payout to a connected account for a completed job.

        Args:
            account_id (str): Stripe Connect Account ID.
            amount (float): The total amount for the job (in USD).
            job_id (int): The job ID for reference.
            posting_fee (float): The fee for posting the job.

        Returns:
            dict: Payout details.
        """
        try:
            # Calculate the net amount to transfer
            net_amount = int((amount - posting_fee) * 100)

            # Create the payout to the connected account
            transfer = stripe.Transfer.create(
                amount=net_amount,
                currency='usd',
                description=f"Payment for #{str(job_id).zfill(5)} job",
                destination=account_id,
                transfer_group=f"#{job_id}"
            )

            return transfer
        except Exception as ex:
            print(f"Unexpected error during payout creation: {str(ex)}")
            raise ex
