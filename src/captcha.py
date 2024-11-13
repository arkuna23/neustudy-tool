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

    def is_seccess(self) -> bool:
        return self.repCode == "0000"


@dataclass
class CaptchaCheck:
    repCode: str
    repMsg: str | None
    success: bool

    def is_success(self) -> bool:
        return self.repCode == "0000"


def encode_point(x: float, secret: str) -> str:
    json_str = dumps({"x": x, "y": CAPTCHA_Y}, separators=(",", ":"))

    return encrypt(json_str, secret)


def decode_point(encoded: str, secret: str) -> tuple[float, int]:
    json_str = decrypt(encoded, secret)
    point = loads(json_str)

    return point["x"], point["y"]


async def get_captcha(session: ClientSession) -> Captcha:
    response = await session.post(
        f"{URL_BASE}/system/captcha/get", json={"captchaType": "blockPuzzle"}
    )
    data = await response.json()
    if not data["success"]:
        raise Exception("Failed to get captcha")
    resp = filter_fields(data["repData"], Captcha)
    return Captcha(repCode=data["repCode"], **resp)


async def check_captcha(session: ClientSession, token: str, point: str) -> CaptchaCheck:
    response = await session.post(
        f"{URL_BASE}/system/captcha/check",
        json={"captchaType": "blockPuzzle", "token": token, "pointJson": point},
    )
    data = await response.json()
    return CaptchaCheck(**filter_fields(data, CaptchaCheck))


@dataclass
class RecognizeResult:
    width: int
    x: int
    x_right: int


def recognize_captcha(bg: bytes, target: bytes) -> RecognizeResult:
    import cv2
    import numpy as np

    bg_img = cv2.imdecode(np.frombuffer(bg, np.uint8), cv2.IMREAD_ANYCOLOR)
    target_img = cv2.imdecode(np.frombuffer(target, np.uint8), cv2.IMREAD_ANYCOLOR)

    bg_can = cv2.Canny(bg_img, 100, 200)
    target_can = cv2.Canny(target_img, 100, 200)

    bg_res = cv2.cvtColor(bg_can, cv2.COLOR_GRAY2RGB)
    target_res = cv2.cvtColor(target_can, cv2.COLOR_GRAY2RGB)

    res = cv2.matchTemplate(bg_res, target_res, cv2.TM_CCOEFF_NORMED)
    x = cv2.minMaxLoc(res)[-1][0]
    return RecognizeResult(bg_img.shape[1], x, x + target_img.shape[1])
