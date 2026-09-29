import re
from fastapi import HTTPException

PHONE_HINT = "enter valid ph. no."


def is_valid_indian_mobile(value: str | None) -> bool:
    if value is None or str(value).strip() == "":
        return False
    raw = re.sub(r"[\s\-]", "", str(value).strip())
    if raw.startswith("+91"):
        raw = raw[3:]
    elif raw.startswith("91") and len(raw) == 12:
        raw = raw[2:]
    if len(raw) != 10 or not raw.isdigit():
        return False
    number = int(raw)
    return 6000000000 <= number <= 9999999999


def normalize_phone(value: str | None, required: bool = False) -> str | None:
    if value is None or str(value).strip() == "":
        if required:
            raise HTTPException(status_code=422, detail=PHONE_HINT)
        return None
    raw = re.sub(r"[\s\-]", "", str(value).strip())
    if raw.startswith("+91"):
        raw = raw[3:]
    elif raw.startswith("91") and len(raw) == 12:
        raw = raw[2:]
    if len(raw) != 10 or not raw.isdigit():
        raise HTTPException(status_code=422, detail=PHONE_HINT)
    number = int(raw)
    if number < 6000000000 or number > 9999999999:
        raise HTTPException(status_code=422, detail=PHONE_HINT)
    return raw
