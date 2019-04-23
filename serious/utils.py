from typing import Collection, Mapping, Type


def _get_constructor(type_: Type) -> Type:
    return type_.__origin__


def _get_type_origin(type_):
    return getattr(type_, '__origin__', type_)


def _hasargs(type_, *args):
    try:
        res = all(arg in type_.__args__ for arg in args)
    except AttributeError:
        return False
    else:
        return res


def _isinstance_safe(o, t):
    try:
        result = isinstance(o, t)
    except Exception:
        return False
    else:
        return result


def _is_optional(type_):
    return _hasargs(type_, type(None))


def _is_mapping(type_):
    return issubclass(_get_type_origin(type_), Mapping)


def _is_collection(type_):
    return issubclass(_get_type_origin(type_), Collection)
