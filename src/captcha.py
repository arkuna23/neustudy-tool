from dataclasses import dataclass
from json import dumps, loads

from aiohttp import ClientSession

from .consts import *
from .crypto import decrypt, encrypt
from .util import filter_fields


@dataclass
class Captcha:
    repCode: str
    secretKey: str
    originalImageBase64: str
    jigsawImageBase64: str
    token: str

@dataclass
class CaptchaCheck:
    repCode: str
    repMsg: str|None
    success: bool

def encode_point(x: float, secret: str) -> str:
    json_str = dumps({
        'x': x,
        'y': CAPTCHA_Y
    }, separators=(',', ':'))

    return encrypt(json_str, secret)

def decode_point(encoded: str, secret: str) -> tuple[float, int]:
    json_str = decrypt(encoded, secret)
    point = loads(json_str)

    return point['x'], point['y']

async def get_captcha(session: ClientSession) -> Captcha:
    response = await session.post(
        f'{URL_BASE}/system/captcha/get',
        json={"captchaType":"blockPuzzle"}
    )
    data = await response.json()
    if not data['success']:
        raise Exception('Failed to get captcha')
    resp = filter_fields(data['repData'], Captcha)
    return Captcha(repCode=data['repCode'], **resp)

async def check_captcha(session: ClientSession, token: str, point: str) -> CaptchaCheck:
    response = await session.post(
        f'{URL_BASE}/system/captcha/check',
        json={
            "captchaType":"blockPuzzle",
            "token": token, 
            "pointJson": point
        }
    )
    data = await response.json()
    return CaptchaCheck(**filter_fields(data, CaptchaCheck))
