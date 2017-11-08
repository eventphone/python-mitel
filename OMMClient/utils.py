import rsa
import base64


def encrypt_pin(pin, modulus, exponent):
    # Known weak implementation of encryption using ECB
    # "Chaining mode such as ECB makes no sense for RSA, unless you are doing it wrong."
    # Quote from https://stackoverflow.com/questions/2855326
    # Necessary for OMM to compare PIN of a user
    pub_key = rsa.PublicKey(int(modulus, 16), int(exponent, 16))
    crypted = rsa.encrypt(pin, pub_key=pub_key)
    return base64.b64encode(crypted)
