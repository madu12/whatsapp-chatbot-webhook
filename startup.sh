#!/bin/bash

# Logging
echo "Starting startup.sh script"

# Update package lists
apt-get update

# Install ffmpeg
apt-get install -y ffmpeg

# Logging
echo "ffmpeg installed"

# Start the Flask app
python3 app.py

# Logging
echo "Flask app started"
