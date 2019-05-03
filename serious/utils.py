from typing import Collection, Mapping, Any, Union, List, Type

DataClass = Any
Primitive = Union[Mapping, List, str, int, float, bool, None]


def _get_type_origin(type_: Type) -> Type:
    return getattr(type_, '__origin__', type_)


def _hasargs(type_: Type, *args) -> bool:
    return all(arg in type_.__args__ for arg in args)


def _is_optional(type_: Type) -> bool:
    return _hasargs(type_, type(None))


def _is_mapping(type_: Type) -> bool:
    return issubclass(_get_type_origin(type_), Mapping)


def _is_collection(type_: Type) -> bool:
    return issubclass(_get_type_origin(type_), Collection)


def _class_path(cls: Type) -> str:
    return f'{cls.__module__}.{cls.__qualname__}'
