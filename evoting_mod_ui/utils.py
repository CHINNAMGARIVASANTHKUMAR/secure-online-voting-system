import hashlib
import json
import random
from datetime import datetime, date


def hash_text(value: str) -> str:
    return hashlib.sha256(value.strip().encode('utf-8')).hexdigest()


def is_valid_aadhaar(aadhaar: str) -> bool:
    return aadhaar.isdigit() and len(aadhaar) == 12 and aadhaar != '0' * 12


def is_valid_mobile(mobile: str) -> bool:
    digits = ''.join(ch for ch in mobile if ch.isdigit())
    return len(digits) == 10 and digits != '0' * 10


def normalize_mobile(mobile: str) -> str:
    digits = ''.join(ch for ch in mobile if ch.isdigit())
    return digits[-10:]


def is_valid_unique_id(unique_id: str) -> bool:
    return unique_id.isdigit() and len(unique_id) == 9 and unique_id[0] != '0' and unique_id != '0' * 9


def generate_unique_id(existing_checker) -> str:
    while True:
        value = str(random.randint(100_000_000, 999_999_999))
        if existing_checker(value):
            return value


def is_18_plus(dob_str: str) -> bool:
    dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return age >= 18


def utc_now_str() -> str:
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')


def to_json(data: dict) -> str:
    return json.dumps(data, sort_keys=True)
