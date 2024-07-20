class GeneralUtils:
    def __init__(self):
        pass

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
