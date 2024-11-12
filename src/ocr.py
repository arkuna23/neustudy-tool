import os
import platform
from io import BytesIO
from os import path
from subprocess import Popen
from zipfile import ZipFile

from aiohttp import ClientSession

from .consts import *
from .util import ensure_data_dir


def get_zip_name() -> str:
    current_system = platform.system()
    arch = platform.machine()
    match current_system:
        case 'Windows':
            return f'{arch}-pc-windows-msvc-inline.zip'
        case 'Linux':
            return f'{arch}-unknown-linux-gnu-inline.zip'
        case 'Darwin':
            return f'{arch}-apple-darwin-inline.zip'
        case _:
            raise Exception('Unsupported OS')

def get_bin_name() -> str:
    current_system = platform.system()
    match current_system:
        case 'Windows':
            return "ddddocr.exe"
        case 'Linux' | "Darwin":
            return "ddddocr"
        case _:
            raise Exception('Unsupported OS')

async def download_server(session: ClientSession):
    zip_name = get_zip_name()
    url = f'{OCR_SERVER_URL}/{zip_name}'
    print(f'下载地址: {url}')
    resp = await session.request('GET', url)
    data = await resp.read()
    with ZipFile(BytesIO(data)) as z:
        print(f'解压{zip_name}中...')
        bin = get_bin_name()
        for name in z.namelist():
            if name.endswith(bin):
                z.extract(name, DATA_DIR)
                break

async def ensure_server():
    ensure_data_dir()
    bin = f'{DATA_DIR}/{get_bin_name()}'
    if not path.exists(bin):
        print('未检测到OCR后端，开始下载...')
        async with ClientSession() as session:
            await download_server(session)

    if not os.access(bin, os.X_OK):
        os.chmod(bin, 0o755)

class OCRServer:
    process: Popen

    def __init__(self, addr: str = '127.0.0.1', port: int = 9898):
        self.addr = addr
        self.port = port
        self.base_url = f'http://{addr}:{port}'
        self.session = ClientSession(trust_env=True)

    async def start(self):
        await ensure_server()
        bin = get_bin_name()
        self.process = Popen([
            f'{DATA_DIR}/{bin}', 
            '-a', self.addr, 
            '-p', str(self.port), 
            '--slide-match'
        ])

    def stop(self):
        self.process.kill()

    async def slide_match(self, target_b64:str, bg_b64:str):
        resp = await self.session.post(f"{self.base_url}/match/b64/json", json={
            'target': target_b64,
            "background": bg_b64
        })
        return await resp.json()
