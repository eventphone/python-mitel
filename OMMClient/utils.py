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

def convert_ipui(ipui):
    if len(ipui) is not 10:
        return False
    emcHex = ipui[:5]
    psnHex = ipui[-5:]
    emc = str(int(emcHex, 16)).zfill(5)
    psn = str(int(psnHex, 16)).zfill(7)
    m = 1
    chksum = 0
    emcpsn = emc + psn
    for c in emcpsn:
        chksum += int(c) * m
        m += 1
    chkdgt = chksum % 11
    if chkdgt is 10:
        chkdgt = '*'
    return '%s%s%s' % (emc, psn, chkdgt)
