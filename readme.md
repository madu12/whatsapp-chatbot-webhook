# WhatsApp Chatbot for Home Services

Welcome to the WhatsApp Chatbot for Home Services! This chatbot helps users post jobs, find jobs, and get assistance with various tasks related to home services.

## Features

- **Post Job**: Users can post new job listings with details such as job category, description, location, date, time, and payment information.
- **Find Job**: Users can search for available job listings based on their preferences.
- **Help**: Users can get assistance and information on how to use the chatbot.

## How to Use

### Save Our Number

Save our WhatsApp number: +15556203184

### Send a Message

Send a message with the text "Hi" to our contact. This initial message will automatically register you in our system and activate the chatbot. You'll receive a welcome message and further guidance.

### Use Commands

- **Post Job**: Type "Post Job" to start the process of posting a new job. The chatbot will guide you through providing details such as job category, description, location, date, time, and payment information.
- **Find Job**: Type "Find Job" to search for available job listings. The chatbot will ask for your preferences and provide a list of matching jobs.
- **Help**: Type "Help" if you need assistance or more information on how to use the chatbot. The chatbot will provide a list of available commands and instructions for each feature.

## Installation and Setup

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/whatsapp-chatbot.git
    cd whatsapp-chatbot
    ```

2. Create and activate a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Set up environment variables:
    Create a `.env` file in the root directory and add the following variables:
    ```
    DATABASE_USERNAME=your_db_username
    DATABASE_PASSWORD=your_db_password
    DATABASE_SERVER=your_db_server
    DATABASE_NAME=your_db_name
    DATABASE_DRIVER=your_db_driver
    DIALOGFLOW_CX_CREDENTIALS_JSON=your_dialogflow_credentials_json
    DIALOGFLOW_CX_AGENTID=your_dialogflow_agent_id
    DIALOGFLOW_CX_LOCATION=your_dialogflow_location
    WHATSAPP_TOKEN=your_whatsapp_token
    VERIFY_TOKEN=your_verify_token
    STRIPE_SECRET_KEY=your_stripe_secret_key
    WEBSITE_URL=your_website_url
    CLASSIFICATION_MODEL_API_URL=your_classification_model_api_url
    CLASSIFICATION_MODEL_API_KEY=your_classification_model_api_key
    GOOGLE_MAPS_API_KEY=your_google_maps_api_key
    ```

5. Run the application:
    ```bash
    python app.py
    ```

6. Access the application:
    Open your web browser and go to `http://localhost:8000`.

## Database Setup

### Table Creation SQL Scripts

```sql
CREATE TABLE users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    phone_number NVARCHAR(15) NOT NULL UNIQUE,
    created_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
    updated_at DATETIMEOFFSET
);

CREATE TABLE categories (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(255) NOT NULL UNIQUE
);

CREATE INDEX idx_category_name ON categories(name);

CREATE TABLE addresses (
    id INT IDENTITY(1,1) PRIMARY KEY,
    street NVARCHAR(255),
    city NVARCHAR(255) NOT NULL,
    state NVARCHAR(255) NOT NULL,
    zip_code NVARCHAR(10) NOT NULL,
    country NVARCHAR(255) NOT NULL DEFAULT 'USA'
);

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

CREATE TABLE chat_sessions (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    job_id INT FOREIGN KEY REFERENCES jobs(id),
    job_type NVARCHAR(255),
    user_id INT NOT NULL FOREIGN KEY REFERENCES users(id),
    created_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET()
);

CREATE INDEX idx_chat_session_id ON chat_sessions(id);
