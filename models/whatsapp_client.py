import requests
import io
import pydub
import soundfile as sf
import speech_recognition as sr
from config import WHATSAPP_TOKEN, LANGUAGE

class WhatsAppClient:
    def __init__(self):
        self.whatsapp_token = WHATSAPP_TOKEN
        self.language = LANGUAGE

    def get_media_url(self, media_id):
        headers = {
            "Authorization": f"Bearer {self.whatsapp_token}",
        }
        url = f"https://graph.facebook.com/v19.0/{media_id}/"
        response = requests.get(url, headers=headers)
        return response.json()["url"]

    def download_media_file(self, media_url):
        headers = {
            "Authorization": f"Bearer {self.whatsapp_token}",
        }
        response = requests.get(media_url, headers=headers)
        return response.content

    def convert_audio_bytes(self, audio_bytes):
        ogg_audio = pydub.AudioSegment.from_ogg(io.BytesIO(audio_bytes))
        ogg_audio = ogg_audio.set_sample_width(4)
        wav_bytes = ogg_audio.export(format="wav").read()
        audio_data, sample_rate = sf.read(io.BytesIO(wav_bytes), dtype="int32")
        sample_width = audio_data.dtype.itemsize
        audio = sr.AudioData(audio_data, sample_rate, sample_width)
        return audio

    def recognize_audio(self, audio_bytes):
        recognizer = sr.Recognizer()
        audio_text = recognizer.recognize_google(audio_bytes, language=self.language)
        return audio_text

    def send_whatsapp_message(self, phone_number_id, from_number, message, interactive=False):
        headers = {
            "Authorization": f"Bearer {self.whatsapp_token}",
            "Content-Type": "application/json",
        }
        url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": from_number,
        }
        if interactive:
            data.update({"type": "interactive", "interactive": message["interactive"]})
        else:
            data.update(message)
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
