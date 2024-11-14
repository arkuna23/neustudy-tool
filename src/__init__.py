from base64 import b64decode
from enum import Enum
from typing import AsyncGenerator

from aiohttp.client import ClientSession

from src.api import Course, SignRecord, get_all_courses, get_sign_record, sign
from src.auth import Account, LoginInfo, SessionInfo, get_tenant_id, login_user
from src.captcha import (check_captcha, encode_point, get_captcha,
                         recognize_captcha)


class LoginState(Enum):
    GetCapcha = 1
    RecognizeCapcha = 2
    CheckCaptcha = 3
    GetTenant = 4
    Login = 5
    RetryCaptcha = 6

async def login(
    session: ClientSession, account: Account, captcha_retry = 0
) -> AsyncGenerator[LoginState | tuple[SessionInfo, LoginInfo], None]:
    yield LoginState.GetTenant
    t_id = await get_tenant_id(session, account.tenant)
    session.headers["tenant-id"] = t_id

    yield LoginState.GetCapcha
    while True:
        captcha = await get_captcha(session)

        yield LoginState.RecognizeCapcha
        point = recognize_captcha(
            b64decode(captcha.originalImageBase64), b64decode(captcha.jigsawImageBase64)
        )
        x = (point.x / point.width) * 310

        yield LoginState.CheckCaptcha
        resp = await check_captcha(
            session, captcha.token, encode_point(x, captcha.secretKey)
        )
        if not resp.success:
            captcha_retry -= 1
            if captcha_retry < 0:
                raise Exception(f"Failed to check captcha: {resp}")

            yield LoginState.RetryCaptcha
        else:
            break

    yield LoginState.Login
    info = await login_user(
        session, captcha.secretKey, x, captcha.token, account
    )
    sess = info.to_session_info(session)
    sess.set_session(session)
    yield sess, info

async def sign_all_courses(
    session: ClientSession, user_id: str
) -> AsyncGenerator[tuple[Course, SignRecord], None]:
    courses = await get_all_courses(session)
    for course in courses:
        record = await get_sign_record(session, user_id, course.teachClassId)
        if record.id:
            yield course, record
            await sign(session, record, user_id)

