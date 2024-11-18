import os
from base64 import b64decode, b64encode
from urllib.parse import quote, unquote
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from config import AES_KEY, AES_IV
class GeneralUtils:
    def __init__(self):
        # Fetch and decode AES_KEY and AES_IV
        self.aes_key = b64decode(AES_KEY)
        self.aes_iv = b64decode(AES_IV)

    def get_address_index(self, address):
        """
        Generate an address index by concatenating and formatting address components.

        Args:
            address (dict): A dictionary containing address components.

        Returns:
            str: The generated address index.
        """
        address_index = ''

        for key, value in address.items():
            if value:
                formatted_value = str(value).upper().replace(' ', '').replace('-', '').replace('/', '').replace('.', '').replace('&', '').replace('#', '')
                address_index += formatted_value

        return address_index

    def encrypt_aes(self, value):
        """Encrypt a value."""
        # Create AES cipher in CBC mode
        cipher = Cipher(algorithms.AES(self.aes_key), modes.CBC(self.aes_iv))
        encryptor = cipher.encryptor()

        # Pad the value to match AES block size
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(value.encode()) + padder.finalize()

        # Encrypt the padded data
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        # Return as Base64 string for storage
        return b64encode(encrypted_data).decode('utf-8')

    def decrypt_aes(self, encrypted_value):
        """Decrypt an encrypted value."""
        # Convert Base64 string back to bytes
        encrypted_data = b64decode(encrypted_value)

        # Create AES cipher in CBC mode
        cipher = Cipher(algorithms.AES(self.aes_key), modes.CBC(self.aes_iv))
        decryptor = cipher.decryptor()

        # Decrypt the data
        decrypted_padded_data = decryptor.update(encrypted_data) + decryptor.finalize()

        # Remove padding to get the original data
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        decrypted_data = unpadder.update(decrypted_padded_data) + unpadder.finalize()

        return decrypted_data.decode()
    
    def encrypt_aes_url_safe(self, value):
        encrypted_data = self.encrypt_aes(value, self.aes_key, self.aes_iv)
        return quote(encrypted_data)

    def decrypt_aes_url_safe(self,encrypted_value):
        encrypted_data = unquote(encrypted_value)
        return self.decrypt_aes(encrypted_data, self.aes_key, self.aes_iv)