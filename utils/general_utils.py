from cryptography.fernet import Fernet
from config import ENCRYPTION_KEY
class GeneralUtils:
    def __init__(self):
        self.encryption_key = ENCRYPTION_KEY
        self.fernet = Fernet(self.encryption_key)

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

    def encrypt_data(self, data):
        """
        Encrypt data using AES encryption (Fernet).

        Args:
            data (str): The data to encrypt.

        Returns:
            str: The encrypted data in base64 format.
        """
        if not isinstance(data, str):
            raise ValueError("Data to be encrypted must be a string.")
        
        encrypted_data = self.fernet.encrypt(data.encode())
        return encrypted_data

    def decrypt_data(self, encrypted_data):
        """
        Decrypt data using AES encryption (Fernet).

        Args:
            encrypted_data (str): The encrypted data in base64 format.

        Returns:
            str: The decrypted data.
        """
        if not isinstance(encrypted_data, str):
            raise ValueError("Encrypted data must be a string.")
        
        decrypted_data = self.fernet.decrypt(encrypted_data)
        return decrypted_data.decode()