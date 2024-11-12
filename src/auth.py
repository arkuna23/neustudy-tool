import json

from aiohttp import ClientSession
from attr import dataclass

from .consts import *
from .crypto import encrypt


@dataclass
class LoginInfo:
    userId: str
    tenantId: str
    accessToken: str
    refreshToken: str
    expiresTime: int

async def get_tenant_id(session: ClientSession, name: str) -> str:
    resp = await session.get(f'{URL_BASE}/system/tenant/get-id-by-name', params={
        'name': name
    })
    data = await resp.json()
    return data['data']

async def login(
        session: ClientSession,
        secret: str,
        captcha_x: float,
        captcha_token: str,
        tenant_name: str,
        username: str,
        password: str
) -> LoginInfo:
    json_data = json.dumps({
        "x": captcha_x,
        "y": CAPTCHA_Y
    }, ident=(',', ':'))
    captcha_ver = encrypt(
        captcha_token + '---' + json_data,
    secret)

    resp = await session.post(f'{URL_BASE}/system/auth/login', json={
        "tenantName": tenant_name,
        "username": username,
        "password": password,
        "captchaVerification": captcha_ver,
        "rememberMe": True
    })
    json_data = await resp.json()
    if json_data['code'] != 0:
        raise Exception('Failed to login')

    return LoginInfo(**json_data['data'])
