from argparse import ArgumentParser, Namespace
from asyncio import run

from aiohttp import ClientSession
from colorama import Fore

from src import LoginState, login, sign_all_courses
from src.api import UnauthorizedException, get_unread_count
from src.auth import Account, SessionInfo, load_account, load_session_config
from src.util import ensure_data_dir

# log functions

def warn(text: str):
    print(f"{Fore.YELLOW}{text}{Fore.RESET}")

def error(text: str):
    print(f"{Fore.RED}{text}{Fore.RESET}")

def info(text: str):
    print(f"{Fore.WHITE}{text}{Fore.RESET}")

def success(text: str):
    print(f"{Fore.GREEN}{text}{Fore.RESET}")


# main functions

def parse_account(args: str) -> Account:
    """Parse account from command line arguments, for example: --account tenant,username,password"""
    tenant, username, password = args.split(',')
    account = Account(tenant, username, password)
    account.save()
    return account

async def login_account(session: ClientSession, account: Account) -> SessionInfo:
    """Login with account from command line arguments"""

    login_gene = login(session, account, 5)
    sess_info = None
    async for state in login_gene:
        match state:
            case LoginState.GetCapcha:
                info("Getting captcha...")
            case LoginState.RecognizeCapcha:
                info("Recognizing captcha...")
            case LoginState.CheckCaptcha:
                info("Checking captcha...")
            case LoginState.RetryCaptcha:
                warn("Retrying captcha...")
            case LoginState.Login:
                info("Logging in...")
            case r if isinstance(r, tuple):
                sess_info = r[0]
                sess_info.save()
                success("Logged in, session saved.")

    assert sess_info
    return sess_info


async def main():
    parser = ArgumentParser()
    parser.add_argument('--account', '-a', type=str, help="Your Account, format: tenant,username,password")
    parser.add_argument("--sign-all", action='store_true')
    args = parser.parse_args()
    ensure_data_dir()

    async with ClientSession(trust_env=True) as session:
        if args.account:
            account = parse_account(args.account)
            sess_info = await login_account(session, account)
        else:
            sess_info = load_session_config(session)
            if sess_info:
                try:
                    await get_unread_count(session)
                except UnauthorizedException:
                    warn("Session expired, re-login...")
                    sess_info = None

            if not sess_info:
                account = load_account()
                if not account:
                    error("Could not find account config.")
                    warn("Please provide an account.")
                    print()
                    parser.print_help()
                    return
                sess_info = await login_account(session, account)

        if args.sign_all:
            count = 0
            async for course, _ in sign_all_courses(session, sess_info.userId):
                count += 1
                info(f"Signing {course.className}...")

            if count > 0:
                success(f"Signed {count} courses.")
            else:
                info("No courses to sign.")
        else:
            info("No action specified.")

if __name__ == "__main__":
    run(main())
