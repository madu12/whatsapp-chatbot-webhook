# WhatsApp Chatbot for Home Services

Welcome to the WhatsApp Chatbot for Home Services! This chatbot helps users post jobs, find jobs, and get assistance with various tasks related to home services.

## Features

- **Post Job**: Users can post new job listings with details such as job category, description, location, date, time, and payment information.
- **Find Job**: Users can search for available job listings based on their preferences.
- **Help**: Users can get assistance and information on how to use the chatbot.

## How to Use

### Save Our Number

Save our WhatsApp number: +15550375664

### Send a Message

Send a message with the text "Hi" to our contact. This initial message will automatically register you in our system and activate the chatbot. You'll receive a welcome message and further guidance.

### Use Commands

- **Post Job**: Type "Post Job" to start the process of posting a new job. The chatbot will guide you through providing details such as job category, description, location, date, time, and payment information.
- **Find Job**: Type "Find Job" to search for available job listings. The chatbot will ask for your preferences and provide a list of matching jobs.
- **Help**: Type "Help" if you need assistance or more information on how to use the chatbot. The chatbot will provide a list of available commands and instructions for each feature.

## Installation and Setup

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)

### Clone the Repository

```bash
git clone https://github.com/madu12/whatsapp-chatbot.git
cd whatsapp-chatbot
```

### Create and Activate a Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
```

### Install the Required Dependencies
```bash
pip install -r requirements.txt
```

### Set Up Environment Variables
Create a .env file in the root directory and add the following variables:
```

DATABASE_DRIVER=ODBC Driver 18 for SQL Server
DATABASE_SERVER=your_db_server
DATABASE_NAME=your_db_name
DATABASE_USERNAME=your_db_username
DATABASE_PASSWORD=your_db_password
DIALOGFLOW_CX_CREDENTIALS_JSON=your_dialogflow_credentials_json
DIALOGFLOW_CX_AGENTID=your_dialogflow_agent_id
DIALOGFLOW_CX_LOCATION=your_dialogflow_location
WHATSAPP_CHATBOT_PHONE_NUMBER=your_whatsapp_business_api_phone_number
WHATSAPP_TOKEN=your_whatsapp_token
WHATSAPP_VERIFY_TOKEN=your_whatsapp_verify_token
STRIPE_SECRET_KEY=your_stripe_secret_key
WEBSITE_URL=your_website_url
CLASSIFICATION_MODEL_API_URL=your_classification_model_api_url
CLASSIFICATION_MODEL_API_KEY=your_classification_model_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
ENCRYPTION_KEY=your_encryption_key
```

### Database Setup
Ensure your database is set up and running. Use the following SQL queries to create the necessary tables:
```sql
-- Create 'users' table if it doesn't exist
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' AND xtype='U')
BEGIN
    CREATE TABLE users (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(255) NOT NULL,
        phone_number NVARCHAR(MAX) NOT NULL UNIQUE,
        created_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
        updated_at DATETIMEOFFSET
    );
END;

-- Create 'categories' table if it doesn't exist
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='categories' AND xtype='U')
BEGIN
    CREATE TABLE categories (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(255) NOT NULL UNIQUE
    );
    CREATE INDEX idx_category_name ON categories(name);
END;

-- Create 'addresses' table if it doesn't exist
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='addresses' AND xtype='U')
BEGIN
    CREATE TABLE addresses (
        id INT IDENTITY(1,1) PRIMARY KEY,
        street NVARCHAR(255),
        city NVARCHAR(255) NOT NULL,
        state NVARCHAR(255) NOT NULL,
        zip_code NVARCHAR(10) NOT NULL,
        country NVARCHAR(255) NOT NULL DEFAULT 'USA',
        address_index VARCHAR(255) NOT NULL,
        user_id INT NOT NULL FOREIGN KEY REFERENCES users(id)
    );
    CREATE INDEX idx_address_index ON addresses(address_index);
END;

-- Create 'jobs' table if it doesn't exist
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='jobs' AND xtype='U')
BEGIN
    CREATE TABLE jobs (
        id INT IDENTITY(1,1) PRIMARY KEY,
        job_description NVARCHAR(255) NOT NULL,
        category_id INT NOT NULL FOREIGN KEY REFERENCES categories(id),
        date_time DATETIMEOFFSET NOT NULL,
        amount DECIMAL(10,2) NOT NULL,
        posting_fee DECIMAL(10,2),
        zip_code NVARCHAR(10) NOT NULL,
        posted_by INT NOT NULL FOREIGN KEY REFERENCES users(id),
        accepted_by INT FOREIGN KEY REFERENCES users(id),
        payment_id NVARCHAR(255),
        status NVARCHAR(255) DEFAULT 'pending',
        payment_status NVARCHAR(255) DEFAULT 'unpaid',
        address_id INT FOREIGN KEY REFERENCES addresses(id),
        payment_intent NVARCHAR(255),
        payment_transfer_id NVARCHAR(255),
        created_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
        updated_at DATETIMEOFFSET
    );
    CREATE INDEX idx_job_status ON jobs(status);
    CREATE INDEX idx_job_date_time ON jobs(date_time);
    CREATE INDEX idx_job_category_id ON jobs(category_id);
END;

-- Create 'chat_sessions' table if it doesn't exist
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='chat_sessions' AND xtype='U')
BEGIN
    CREATE TABLE chat_sessions (
        id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        job_id INT FOREIGN KEY REFERENCES jobs(id),
        job_type NVARCHAR(255),
        user_id INT NOT NULL FOREIGN KEY REFERENCES users(id),
        created_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET()
    );
    CREATE INDEX idx_chat_session_id ON chat_sessions(id);
END;
```

### Run the Application
```bash
python app.py
```

### Access the Application
Open your web browser and go to http://localhost:8000.

## Webhook Setup

### WhatsApp Webhook

1. Go to the [Facebook Developers](https://developers.facebook.com/) portal.

2. Select your App.

3. Go to the "WhatsApp" product and then "Configuration".

4. Under "Webhook", click "Edit".

5. Enter your server URL followed by /webhook (e.g., https://yourdomain.com/webhook).

6. Enter your WHATSAPP_VERIFY_TOKEN in the "Verify Token" field.

7. Save the changes.

### Dialogflow Webhook

1. Go to the [Dialogflow CX Console](https://dialogflow.cloud.google.com/cx).

2. Choose your Google Cloud project.

3. Select your agent.

4. Select the Manage tab.

5. Click Webhooks.

6. Click Create or click a webhook resource in the list to edit.

7. Enter your server URL followed by /dialogflow_webhook (e.g., https://yourdomain.com/dialogflow_webhook).

8. Click Save.

## Additional Resources

* [Dialogflow Documentation](https://cloud.google.com/dialogflow/cx/docs)

* [WhatsApp Business API Documentation](https://developers.facebook.com/docs/whatsapp)

* [Stripe API Documentation](https://stripe.com/docs/api)

## Troubleshooting

### Common Issues
1. Environment Variables: Ensure all required environment variables are set in the .env file.

2. Database Connection: Verify your database connection string and credentials.

3. Webhook Configuration: Ensure the webhook URL and verify token are correctly configured in the Facebook Developers portal.