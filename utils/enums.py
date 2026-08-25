def enum_or_none(enum_cls, value):
    if not value:
        return None
    try:
        return enum_cls(value)
    except ValueError:
        return None
