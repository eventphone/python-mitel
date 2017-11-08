import rsa
import base64


def encrypt_pin(pin, modulus, exponent):
    # Known weak implementation of encryption using ECB
    # Neccessary for OMMM to compare PIN of a user
    pub_key = rsa.PublicKey(int(modulus, 16), int(exponent, 16))
    crypted = rsa.encrypt(pin, pub_key=pub_key)
    return base64.b64encode(crypted)
