import json
from dataclasses import asdict, dataclass
from os import path
from typing import Any

from aiohttp import ClientSession
from yarl import URL

from .consts import *
from .crypto import encrypt


@dataclass
class SessionInfo:
    tenantId: str
    accessToken: str
    userId: str
    cookies: dict[str, Any]

    def set_session(self, session: ClientSession, update_cookies = False):
        """Set session headers with this session info"""
        if update_cookies:
            session.cookie_jar.update_cookies(self.cookies)
        session.headers['Authorization'] = f"Bearer {self.accessToken}"
        session.headers['tenant-id'] = self.tenantId

    def save(self, dir=DATA_DIR, file="session.json"):
        with open(f"{dir}/{file}", "w") as f:
            f.write(json.dumps(asdict(self), indent=4))

def load_session_config(session: ClientSession, dir=DATA_DIR, file="session.json") -> SessionInfo|None:
    conf_path = f"{dir}/{file}"
    if path.exists(conf_path):
        with open(f"{dir}/{file}", "r") as f:
            data = json.load(f)
            session_info = SessionInfo(**data)
            session_info.set_session(session, True)
            return session_info
    else:
        return None


@dataclass
class LoginInfo:
    userId: str
    tenantId: str
    accessToken: str
    refreshToken: str
    expiresTime: int

    def to_session_info(self, session: ClientSession) -> SessionInfo:
        return SessionInfo(
            tenantId=self.tenantId,
            accessToken=self.accessToken,
            userId=self.userId,
            cookies=dict(session.cookie_jar.filter_cookies(URL(URL_BASE)))
        )


async def get_tenant_id(session: ClientSession, name: str) -> str:
    resp = await session.get(
        f"{URL_BASE}/system/tenant/get-id-by-name", params={"name": name}
    )
    data = await resp.json()
    return data["data"]

@dataclass
class Account:
    tenant: str
    username: str
    password: str

    def save(self, dir=DATA_DIR, file="account.json"):
        with open(f"{dir}/{file}", "w") as f:
            f.write(json.dumps(asdict(self), indent=4))

def load_account(dir=DATA_DIR, file="account.json") -> Account|None:
    conf_path = f"{dir}/{file}"
    if path.exists(conf_path):
        with open(f"{dir}/{file}", "r") as f:
            data = json.load(f)
            return Account(**data)
    else:
        return None

async def login_user(
    session: ClientSession,
    secret: str,
    captcha_x: float,
    captcha_token: str,
    account: Account
) -> LoginInfo:
    json_data = json.dumps({"x": captcha_x, "y": CAPTCHA_Y}, separators=(",", ":"))
    captcha_ver = encrypt(captcha_token + "---" + json_data, secret)

    resp = await session.post(
        f"{URL_BASE}/system/auth/login",
        json={
            "tenantName": account.tenant,
            "username": account.username,
            "password": account.password,
            "captchaVerification": captcha_ver,
            "rememberMe": True,
        },
    )
    json_data = await resp.json()
    if json_data["code"] != 0:
        raise Exception(f"Failed to login: {json_data}")

    return LoginInfo(**json_data["data"])
