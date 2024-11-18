# Home Service Model Server Setup

## 1. Update and Upgrade the System
```bash
sudo apt update && sudo apt upgrade
```
## 2. Install Python and Git
```bash
sudo apt install python3-pip python3-dev git
```
## 3. Clone the Project Repository
```bash
git clone https://github.com/madu12/whatsapp-chatbot-webhook.git
cd whatsapp-chatbot-webhook/
```

## 4. Set Up a Python Virtual Environment
```bash
sudo apt install python3-venv
python3 -m venv .venv
source .venv/bin/activate
```

## 5. Install Project Dependencies
```bash
pip install -r requirements.txt
```

## 6. Install ODBC Driver for SQL Server
```bash
sudo apt-get install unixodbc unixodbc-dev
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list | sudo tee /etc/apt/sources.list.d/msprod.list
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install msodbcsql18
```

## 7. Verify ODBC Installation
```bash
ls /usr/lib/x86_64-linux-gnu/ | grep libodbc
```

## 8. Configure Environment Variables
```bash
vim .env
```
Add the following lines to .env: (Replace this with your details)
```bash
DATABASE_DRIVER=ODBC Driver 18 for SQL Server
DATABASE_SERVER=home-service-db.cd8o0gcak2fi.eu-north-1.rds.amazonaws.com
DATABASE_NAME=home_service_chatbot
DATABASE_USERNAME=admin
DATABASE_PASSWORD=MyStrongPass123
DIALOGFLOW_CX_CREDENTIALS_JSON=
DIALOGFLOW_CX_AGENTID=27151d0b-dc37-4573-bffe-291aa1af4e42
DIALOGFLOW_CX_LOCATION=global
WHATSAPP_CHATBOT_PHONE_NUMBER=177404588791336
WHATSAPP_TOKEN=
WHATSAPP_VERIFY_TOKEN=by31pvbDxnzPeHjFM6vipuRxhQCjdFuD
STRIPE_SECRET_KEY=
WEBSITE_URL=https://relevant-wildly-weevil.ngrok-free.app
CLASSIFICATION_MODEL_API_URL=http://16.171.161.214
CLASSIFICATION_MODEL_API_KEY=b9f1xe8PNi8XetQ0FgIe9y3EMA62d7dr
GOOGLE_MAPS_API_KEY=AIzaSyBcVKO2kDqA7dBJuep2HAJPjyCKFSBKwIA
AES_KEY=rcZc1KhfbQpzMMHY40WZSqVeiAqAQONTXLwHYt/z0hk=
AES_IV=ZaT2Vag6FFq2tiSPqs6zoA==
```

## 9. Train the Machine Learning Model
```bash
python3 train_model.py
```

## 10. Configure Firewall (UFW)
```bash
sudo ufw status
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 8080
sudo ufw allow 5000
sudo ufw allow 5001
```
## 11. Install and Configure Nginx
```bash
sudo apt update 
sudo apt install nginx
sudo vim /etc/nginx/sites-available/whatsapp-chatbot-webhook
```

## 12. Install and Configure Nginx
```bash
server {
    listen 80;
    server_name 51.20.9.94; # Replace this with your server's public IP

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 12. Enable the Nginx Site and Reload
```bash
sudo ln -s /etc/nginx/sites-available/whatsapp-chatbot-webhook /etc/nginx/sites-enabled/
sudo systemctl reload nginx
```

## 13. Install and Configure Gunicorn
```bash
pip install gunicorn
sudo vim /etc/systemd/system/gunicorn.service
```
Add the following content to the Gunicorn service file:
```bash
[Unit]
Description=Gunicorn instance for a Home Service Webhook app
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/whatsapp-chatbot-webhook
ExecStart=/home/ubuntu/whatsapp-chatbot-webhook/.venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```
## 14. Start and enable Gunicorn:
```bash
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
sudo systemctl daemon-reload
sudo journalctl -u gunicorn
```
### This step is optional. If you don't have a custom domain and are using Ngrok's subdomain, setting up the `ngrok.service` as a systemd service is not necessary. Here’s how you should modify the instructions to reflect that:

## 15. Install Ngrok:
```bash
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
   | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
   && echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
   | sudo tee /etc/apt/sources.list.d/ngrok.list \
   && sudo apt update \
   && sudo apt install ngrok
```

## 16. Add Ngrok authentication token:
```bash
   ngrok config add-authtoken 2nSVDPoIWoZQLuqeucLl5QJExWk_4pdT51VwAk7V1MJdkNwxq # Replace this with your ngrok authtoken
```

## 17. Create and configure Ngrok service:
```bash
sudo nano /etc/systemd/system/ngrok.service
```
Add the following content to the ngrok service file:
```bash
[Unit]
Description=Ngrok Service
After=network.target

[Service]
ExecStart=/usr/local/bin/ngrok http --url=harmless-ghoul-lively.ngrok-free.app 5000 # Replace this with your ngrok domain
Restart=on-failure
User=ubuntu
WorkingDirectory=/home/ubuntu

[Install]
WantedBy=multi-user.target
```

## 18. Reload systemd, start, and enable Ngrok service:
```bash
sudo systemctl daemon-reload
sudo systemctl start ngrok
sudo systemctl enable ngrok
sudo systemctl status ngrok
```