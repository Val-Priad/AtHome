def strip_password(value: str) -> str:
    if isinstance(value, str):
        value = value.strip()
    return value
