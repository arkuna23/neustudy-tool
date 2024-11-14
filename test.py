from asyncio import run
from base64 import b64decode

from aiohttp import ClientSession

from _userinfo import *
from src import LoginState, login, sign_all_courses
from src.api import UnauthorizedException
from src.auth import SessionInfo, load_session_config
from src.captcha import recognize_captcha
from src.util import ensure_data_dir


async def check_test():
    with (
        open("test/bg.txt", newline=None) as bg,
        open("test/target.txt", newline=None) as target,
    ):
        bg = bg.read()
        target = target.read()
        bg = b64decode(bg)
        open("test/bg.png", "wb").write(bg)
        target = b64decode(target)
        open("test/target.png", "wb").write(target)
        result = recognize_captcha(bg, target)
        pos_percent = result.x / result.width
        x = pos_percent * 310
        print(x)

async def login_session(session: ClientSession) -> SessionInfo:
        login_gene = login(session, ACC, 5)
        async for state in login_gene:
            match state:
                case LoginState.GetCapcha:
                    print("Getting captcha...")
                case LoginState.RecognizeCapcha:
                    print("Recognizing captcha...")
                case LoginState.CheckCaptcha:
                    print("Checking captcha...")
                case LoginState.RetryCaptcha:
                    print("Retrying captcha...")
                case LoginState.Login:
                    print("Logging in...")
                    break
        ensure_data_dir()
        result = await anext(login_gene)

        sess = None
        if isinstance(result, tuple):
            sess = result[0]
            sess.save()

        assert sess
        return sess

async def sign_all(session: ClientSession, sess: SessionInfo):
    try:
        async for r, _ in sign_all_courses(session, sess.userId):
            print(f"Signing {r.courseName} {r.className}")
    except UnauthorizedException:
        sess = await login_session(session)
        await sign_all(session, sess)

async def main():
    async with ClientSession() as session:
        sess = load_session_config(session)
        if not sess:
            sess = await login_session(session)

        assert sess
        print(sess)


if __name__ == "__main__":
    run(main())
