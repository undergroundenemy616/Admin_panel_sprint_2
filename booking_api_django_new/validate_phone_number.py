import re


def validate_phone_number(phone: str) -> bool:
    try:
        if re.match(r"^\+(?:[0-9]\x20?){6,14}[0-9]$", phone):
            return True
        return False
    except TypeError:
        return False