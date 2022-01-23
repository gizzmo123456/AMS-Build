from common import LockFile
import os
import base64
from Crypto.Cipher import AES as crypto_aes
from Crypto.Random import get_random_bytes
from Crypto.Hash import BLAKE2b

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

    def __init__( self, secrets_path, cipher_name ):
        super().__init__( secrets_path, cipher_name )
        self.hasher = BLAKE2b.new( digest_bits=512, key=self.get_or_create_key(), update_after_digest=True )

    def new( self ):
        self.hasher = BLAKE2b.new( digest_bits=512, key=self.get_or_create_key(), update_after_digest=True )

    def digest( self, data_str ):
        self.hasher.update( data_str.encode() )

        return self.hasher.hexdigest()

class AES( Cipher ):

    def __init__(self, secrets_path, cipher_name, nonce=None):
        super().__init__( secrets_path, cipher_name, 32)

        # might it be worth added __enter__, __exit__ so it can be used with the with statement

    def encrypt( self, bytes_to_encrypt, non_encrypted_bytes=[], in_base64=True):

        cipher = crypto_aes.new( self.get_or_create_key(), crypto_aes.MODE_EAX )

        for non_bytes in non_encrypted_bytes:
            cipher.update( non_bytes )

        encrypted_data, tag = cipher.encrypt_and_digest( bytes_to_encrypt )

        if in_base64:
            return {
                "nonce": base64.b64encode( cipher.nonce ),
                "data": base64.b64encode( encrypted_data ),
                "tag": base64.b64encode( tag )
            }
        else:
            return {
                "nonce": cipher.nonce,
                "data": encrypted_data,
                "tag": tag
            }

        pass

    def decrypt( self, decrypt_values, non_encrypted_data=[], from_base64=True ):

        if from_base64:
            for key in decrypt_values:
                decrypt_values[ key ] = base64.b64decode( decrypt_values[key] )

        cipher = crypto_aes.new( self.get_or_create_key(), crypto_aes.MODE_EAX, nonce=decrypt_values["nonce"] )

        for non_encrypted in non_encrypted_data:
            cipher.update( non_encrypted )

        try:
            return cipher.decrypt_and_verify( decrypt_values["data"], decrypt_values["tag"] )
        except (ValueError, KeyError):
            return None


if __name__ == "__main__":

    import DEBUG
    _print = DEBUG.LOGS.print

    DEBUG.LOGS.init()
    path = "./data/.secrets/"

    data_to_encrypt = b"Helloo World!"
    data_to_not_encrypt = [ b"Header1", b"Header2", b"Header3" ]

    encrypt_cipher = AES( path, "TEST_AES_CIPHER" )
    encrypt_cipher64 = AES( path, "TEST_AES_CIPHER" )

    encrypted_data = encrypt_cipher.encrypt( data_to_encrypt, data_to_not_encrypt, in_base64=False )
    encrypted_data64 = encrypt_cipher64.encrypt( data_to_encrypt, data_to_not_encrypt, in_base64=True )

    _print( "Encrypted data" )
    _print( encrypted_data )
    _print( "Encrypted data 64" )
    _print( encrypted_data64 )

    decrypt_cipher = AES( path, "TEST_AES_CIPHER", nonce=encrypted_data["nonce"])
    decrypt_cipher64 = AES( path, "TEST_AES_CIPHER", nonce=base64.b64decode( encrypted_data64["nonce"] ) )

    decrypted_data = decrypt_cipher.decrypt( encrypted_data, [], from_base64=False )
    decrypted_data64 = decrypt_cipher.decrypt( encrypted_data64, [], from_base64=True )

    _print( "Decrypted data" )
    _print( decrypted_data )
    _print( "Decrypted data 64" )
    _print( decrypted_data64 )



