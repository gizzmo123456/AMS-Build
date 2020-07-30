import base64
from Crypto.Cipher import AES as crypto_aes
from Crypto.Random import get_random_bytes

class AES:

    def __init__(self):
        self.encryption_key = get_random_bytes(16)
        self.cipher = crypto_aes.new(self.encryption_key, crypto_aes.MODE_CTR)
        self.nonce = ""

    def new_cipher(self):
        self.cipher = crypto_aes.new(self.encryption_key, crypto_aes.MODE_CTR, nonce=base64.b64decode(self.nonce) )

    def encrypt(self, str_to_encrypt):
        """ Encrypt using AES CTR

        :param str_to_encrypt:  plain text string to be encrypted
        :return:                encrypted str
        """

        encrypted_bytes = self.cipher.encrypt( str_to_encrypt.encode() )
        self.nonce = base64.b64encode( self.cipher.nonce ).decode("utf-8")

        return base64.b64encode( encrypted_bytes ).decode("utf-8")

    def decrypt(self, str_to_decrypt):
        """ Encrypt using AES CTR

        :param str_to_decrypt:  plain text string to be encrypted
        :return:                encrypted str
        """

        decoded_str = base64.b64decode( str_to_decrypt )

        return "".join( map ( chr, self.cipher.decrypt( decoded_str ) ) )
