def reject_string_with_whitespaces(value: str) -> str:
    if isinstance(value, str) and any(c.isspace() for c in value):
        raise ValueError("There must be no spaces in the password")
    return value
