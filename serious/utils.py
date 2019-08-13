import re
from typing import Type, Any

Dataclass = Any  # a dataclass instance


def class_path(cls: Type) -> str:
    """Returns a fully qualified type name."""
    return f'{cls.__module__}.{cls.__qualname__}'


first_cap_re = re.compile(r'(.)([A-Z][a-z]+)')
all_cap_re = re.compile(r'([a-z0-9])([A-Z])')
digit_re = re.compile(r'([a-z])([0-9])')


def camel_to_snake(camel: str) -> str:
    s1 = first_cap_re.sub(r'\1_\2', camel)
    s2 = all_cap_re.sub(r'\1_\2', s1).lower()
    return re.compile(r'([a-z])([0-9])').sub(r'\1_\2', s2)


def snake_to_camel(snake: str) -> str:
    first, *others = filter(bool, snake.split('_'))
    return ''.join([first.lower(), *map(str.title, others)])
