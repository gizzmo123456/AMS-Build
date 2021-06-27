from common import LockFile
import os
import base64
from Crypto.Cipher import AES as crypto_aes
from Crypto.Random import get_random_bytes
from Crypto.Hash import BLAKE2b

import hashlib

class Cipher:

    def __init__( self, secrets_path, cipher_name, key_length=16 ):

        self.name = cipher_name
        self.path = secrets_path
        self.keys = ".keys/"
        self.key_len = key_length - (key_length % 8)    # make sure the key is a multiple of 8 (not that it guarantees anything)

    def get_or_create_key(self):

        if not os.path.exists( self.path ):
            os.mkdir( self.path )

        if not os.path.exists( self.path + self.keys ):
            os.mkdir( self.path+self.keys )

        key_path = "{0}{1}.{2}".format(self.path, self.keys, self.name)

        if os.path.exists( key_path ):
            # return the key.
            with LockFile( key_path, mode='rb' ) as file:
                return file.read()
        else:
            # create a new key.
            key = get_random_bytes(self.key_len)
            with LockFile( key_path, mode='wb' ) as file:
                file.write( key )

            return key


class Hash( Cipher ):

    def __init__( self, secrets_path, cipher_name, key_length=16 ):
        super().__init__( secrets_path, cipher_name, key_length )
        self.hasher = BLAKE2b.new( digest_bits=512, key=self.get_or_create_key(), update_after_digest=True )

    def new( self ):
        self.hasher = BLAKE2b.new( digest_bits=512, key=self.get_or_create_key(), update_after_digest=True )

    def digest( self, data_str ):
        self.hasher.update( data_str.encode() )

        return self.hasher.hexdigest()

    @staticmethod
    def sha1(data_str):
        """ Creates SHA1 hash"""
        s = hashlib.sha1()
        s.update(data_str.encode())
        return s.hexdigest()

# TODO: Update AES to support the base Cipher class
class AES:

    def __init__(self, nonce=None):
        self.encryption_key = get_random_bytes(16)
        self.cipher = crypto_aes.new(self.encryption_key, crypto_aes.MODE_CTR)
        self.nonce = nonce

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
