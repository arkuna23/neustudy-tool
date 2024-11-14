# Neustudy Tool

## Installation

1. Clone the repository

```bash
git clone https://github.com/arkuna23/neustudy-tool.git
```

2. Install dependencies

```bash
cd neustudy-tool
pip install -r requirements.txt
```

3. Enjoy!

## Usage

### Login and authenticate, sign all classes

```bash
python main.py -a <tenant name>,<username>,<password> # login, authenticate your account
python main.py --sign-all # sign all classes
```

or

```bash
python main.py -a <tenant name>,<username>,<password> --sign-all # login, authenticate your account and sign all classes
```

It will save your session in `session.json` file, and account information in `account.json` file, you don't need to login again next time, just use action params(such as `--sign-all`) to do what you want.
