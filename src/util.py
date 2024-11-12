import os
from dataclasses import fields

from .consts import *


def filter_fields(data, data_class):
    valid_fields = {field.name for field in fields(data_class)}
    return {key: value for key, value in data.items() if key in valid_fields}


def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
