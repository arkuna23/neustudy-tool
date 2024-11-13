from base64 import b64decode
from enum import Enum
from typing import AsyncGenerator

from aiohttp.client import ClientSession

from src.auth import LoginInfo, get_tenant_id, login_user
from src.captcha import check_captcha, encode_point, get_captcha, recognize_captcha


class LoginState(Enum):
    GetCapcha = 1
    RecognizeCapcha = 2
    CheckCaptcha = 3
    GetTenant = 4
    Login = 5


async def login(
    session: ClientSession, tenant_name: str, username: str, password: str
) -> AsyncGenerator[LoginState | LoginInfo, None]:
    yield LoginState.GetCapcha
    captcha = await get_captcha(session)

    yield LoginState.RecognizeCapcha
    point = recognize_captcha(
        b64decode(captcha.originalImageBase64), b64decode(captcha.jigsawImageBase64)
    )
    x = (point.x / point.width) * 310  # 计算滑块的中心点在图片宽度的位置百分比

    yield LoginState.CheckCaptcha
    resp = await check_captcha(
        session, captcha.token, encode_point(x, captcha.secretKey)
    )
    if not resp.success:
        raise Exception(f"Failed to check captcha: {resp}")

    yield LoginState.GetTenant
    t_id = await get_tenant_id(session, tenant_name)
    session.headers["tenant-id"] = t_id

    yield LoginState.Login
    info = await login_user(
        session, captcha.secretKey, x, captcha.token, tenant_name, username, password
    )
    session.headers["Authorization"] = f"Bearer {info.accessToken}"
    yield info
