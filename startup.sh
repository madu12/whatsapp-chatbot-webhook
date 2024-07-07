#!/bin/bash

# Install ffmpeg
apt-get update
apt-get install -y ffmpeg

# Start the Flask app
python3 app.py
