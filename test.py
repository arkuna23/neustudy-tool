from asyncio import run
from base64 import b64decode

import aiofiles
import cv2


async def main():
    from src.ocr import OCRServer

    async with aiofiles.open(
        "./test/bg.txt", "r+", encoding="ascii"
    ) as bg, aiofiles.open("./test/target.txt", "r+", encoding="ascii") as t:
        bg_b64 = await bg.readline()
        async with aiofiles.open("./test/bg.png", "wb") as f:
            await f.write(b64decode(bg_b64))
            await f.flush()
        target_b64 = await t.readline()
        async with aiofiles.open("./test/target.png", "wb") as f:
            await f.write(b64decode(target_b64))
            await f.flush()

    async with OCRServer() as server:
        resp = await server.slide_match(
            bg_b64[0:-1],
            target_b64[0:-1],
        )
        img = cv2.imread("./test/bg.png")
        width = img.shape[1]
        cv2.imwrite(
            "./test/out.png",
            img[resp.y1 : resp.y2, (width - resp.x2) : (width - resp.x1)],
        )


if __name__ == "__main__":
    run(main())
