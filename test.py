from asyncio import run
from base64 import b64decode

from aiohttp import ClientSession

from _userinfo import *
from src import LoginState, login
from src.captcha import recognize_captcha


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
        pos_percent = result.x / result.width  # 计算滑块的起始点在图片宽度的位置百分比
        x = pos_percent * 310
        print(x)


async def main():
    async with ClientSession() as session:
        login_gene = login(session, TENANT, USERNAME, PASSWORD)
        async for state in login_gene:
            match state:
                case LoginState.GetCapcha:
                    print("Getting captcha...")
                case LoginState.RecognizeCapcha:
                    print("Recognizing captcha...")
                case LoginState.CheckCaptcha:
                    print("Checking captcha...")
                case LoginState.Login:
                    print("Logging in...")
                    break
        info = await anext(login_gene)
        print(info)


if __name__ == "__main__":
    run(main())
