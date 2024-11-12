from base64 import b64decode, b64encode

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


def encrypt(data: str, secret: str) -> str:
    cipher = AES.new(secret.encode(), AES.MODE_ECB)
    return b64encode(
        cipher.encrypt(pad(data.encode(), AES.block_size))
    ).decode()

def decrypt(data: str, secret: str) -> str:
    cipher = AES.new(secret.encode(), AES.MODE_ECB)
    return unpad(
        cipher.decrypt(b64decode(data)), AES.block_size
    ).decode()
