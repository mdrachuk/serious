"""Descriptors of types used by Serious.

Descriptors are simplifying work with types, enriching them with more contextual information.
This allows to make decisions, like picking a serializer, easier.

They unwrap the generic aliases, get generic parameters from parent classes, simplify optional,
dataclass checks and more.

The data is carried by `TypeDescriptor`s which are created by a call to `serious.descriptors.describe(cls)`.
"""
from __future__ import annotations

__all__ = ['TypeDescriptor', 'describe', 'DescTypes', 'scan_types']

import datetime
import decimal
import uuid
from dataclasses import dataclass, fields, is_dataclass
from types import UnionType, NoneType
from typing import Type, Any, TypeVar, get_type_hints, Dict, Mapping, List, Union, Iterable, Optional, cast, Generic

from .types import FrozenDict, FrozenList

T = TypeVar('T')

GenericParams = Mapping[Any, 'TypeDescriptor']


@dataclass(frozen=True)
class TypeDescriptor:
    """A descriptor of a type unwrapping the aliases, optionals, separating generic parameters,
    extracting the parameters from broader context, etc.

    Type descriptors are mostly used for mapping serializers to particular objects.

    A proper way of creating a `TypeDescriptor` is using the `serious.descriptors.describe(cls)` factory.
    """
    _cls: Type
    parameters: FrozenDict[Any, TypeDescriptor]
    is_optional: bool = False
    is_dataclass: bool = False
    is_typed_dict: bool = False

    @property
    def is_sqlalchemy_model(self):
        from serious.serialization.field_serializers import SQLALCHEMY_INTEGRATION_ENABLED

        if not SQLALCHEMY_INTEGRATION_ENABLED:
            return False

        from sqlalchemy.orm import DeclarativeMeta

        return isinstance(self.cls, DeclarativeMeta)

    @property
    def cls(self):  # Python fails when providing cls as a keyword parameter to dataclasses
        return self._cls

    @property
    def fields(self) -> Mapping[str, TypeDescriptor]:
        """A mapping of all dataclass or typed dict field names to their corresponding Type Descriptors.

        An empty mapping is returned if the object is not a dataclass."""
        if self.is_dataclass:
            types = get_type_hints(self.cls)  # type: Dict[str, Type]
            descriptors = {name: self.describe(type_) for name, type_ in types.items()}
            return {f.name: descriptors[f.name] for f in fields(self.cls)}
        if self.is_typed_dict:
            types = get_type_hints(self.cls)
            descriptors = {name: self.describe(type_) for name, type_ in types.items()}
            return {key: descriptors[key] for key in self.cls.__annotations__}
        if self.is_sqlalchemy_model:
            _fields_names = [p.key for p in self._cls.__mapper__.attrs]
            mapped_types = get_type_hints(self.cls)
            descriptors = {
                name: self.describe(self._sqlalchemy_mapped_type(type_))
                for name, type_ in mapped_types.items()
            }
            for f in _fields_names:
                if f not in descriptors:
                    type_ = self.cls.__mapper__.columns[f].type
                    descriptors[f] = self.describe(_get_sqlalchemy_builtin_type(type_))
            return {f: descriptors[f] for f in _fields_names}
        return {}

    def _sqlalchemy_mapped_type(self, type_) -> Type:
        from sqlalchemy.orm import Mapped

        if issubclass(getattr(type_, "__origin__", NoneType), Mapped):
            return type_.__args__[0]  #type: ignore

        return type_

    def describe(self, type_: Type) -> TypeDescriptor:
        return describe(type_, self.parameters)

    def __repr__(self):
        return f"<TypeDescriptor {str(self)}>"

    def __str__(self):
        results = f""
        if self.is_optional:
            results += "Optional["
        results += getattr(self.cls, "__name__", str(self.cls))
        if self.parameters:
            results += (
                "[" + ", ".join(f"{k}={v}" for k, v in self.parameters.items()) + "]"
            )
        if self.is_optional:
            results += "]"
        return results

def describe(type_: Type, generic_params: Optional[GenericParams] = None) -> TypeDescriptor:
    """Creates a TypeDescriptor for the provided type.

    Optionally generic params can be designated as a mapping of TypeVar to parameter Type or indexes in Dict/List/etc.
    """
    generic_params = generic_params if generic_params is not None else {}
    param = generic_params.get(type_, None)
    if param is not None:
        return param
    return _describe_generic(type_, generic_params)


def _get_sqlalchemy_builtin_type(column_type):
    from sqlalchemy.sql.sqltypes import (
        String, Enum, Text, Unicode, UnicodeText, VARCHAR, NVARCHAR, CHAR, NCHAR, NullType,
        Integer, SmallInteger, BigInteger, Float, Double, REAL, NUMERIC, DECIMAL, Numeric,
        Boolean, DateTime, TIMESTAMP, DATETIME, Date, Time, Interval, LargeBinary, JSON, ARRAY, PickleType, UUID,
    )

    if isinstance(column_type, (String, Enum, Text, Unicode, UnicodeText, VARCHAR, NVARCHAR, CHAR, NCHAR)):
        if isinstance(column_type, Enum):
            return column_type.enum_class  # Return the specific enum class
        return str
    elif isinstance(column_type, (Integer, SmallInteger, BigInteger)):
        return int
    elif isinstance(column_type, (Float, Double, REAL, NUMERIC, DECIMAL)):
        return float
    elif isinstance(column_type, Numeric):
        return decimal.Decimal
    elif isinstance(column_type, Boolean):
        return bool
    elif isinstance(column_type, (DateTime, TIMESTAMP, DATETIME)):
        return datetime.datetime
    elif isinstance(column_type, Date):
        return datetime.date
    elif isinstance(column_type, Time):
        return datetime.time
    elif isinstance(column_type, Interval):
        return datetime.timedelta
    elif isinstance(column_type, LargeBinary):
        return bytes
    elif isinstance(column_type, JSON):
        return dict
    elif isinstance(column_type, ARRAY):
        return list
    elif isinstance(column_type, PickleType):
        raise NotImplementedError("PickleType is not supported")
    elif isinstance(column_type, UUID):
        return uuid.UUID
    elif isinstance(column_type, NullType):
        return type(None)
    else:
        raise NotImplementedError(f"Type {column_type} is not supported")

_any_type_desc = TypeDescriptor(Any, FrozenDict())  # type: ignore
_generic_params: Dict[Type, Dict[int, TypeDescriptor]] = {
    list: {0: _any_type_desc},
    set: {0: _any_type_desc},
    frozenset: {0: _any_type_desc},
    tuple: {0: _any_type_desc, 1: TypeDescriptor(Ellipsis, FrozenDict())},  # type: ignore
    dict: {0: _any_type_desc, 1: _any_type_desc},
    FrozenDict: {0: _any_type_desc, 1: _any_type_desc},
}


def _get_default_generic_params(cls: Type, params: GenericParams) -> GenericParams:
    """Returns mapping of default generic params for the provided cls.

    **Examples**:
     - `dict` -> `{0: <TypeDescriptor cls=Any>, 1: <TypeDescriptor cls=Any>}`;
     - `list` -> `{0: <TypeDescriptor cls=Any>}`;
     - `tuple` -> `{0: <TypeDescriptor cls=Any>, 1: <TypeDescriptor cls=Ellipses>}`.
    """
    for generic, default_params in _generic_params.items():
        if issubclass(cls, generic):
            return default_params
    return params


def _describe_generic(cls: Type, generic_params: GenericParams) -> TypeDescriptor:
    """Creates a TypeDescriptor for Python _GenericAlias, unwrapping it to its origin/

    **Examples**:
     - `Tuple[str]` -> `<TypeDescriptor cls=tuple params={0: <TypeDescriptor cls=str>}>`;
     - `Optional[int]` -> `<TypeDescriptor cls=int is_optional=True>`.
    """
    params: GenericParams = {}
    is_optional = _is_optional(cls)
    if is_optional:
        _args = set(cls.__args__)
        _args.remove(type(None))
        cls = cast(Type, Union[tuple(_args)])

    try:
        is_typed_dict = issubclass(cls, dict) and bool(getattr(cls, '__annotations__', None))
    except TypeError:
        is_typed_dict = False

    if hasattr(cls, '__orig_bases__') and is_dataclass(cls):
        _params: Dict[Any, TypeDescriptor] = {}
        for item in (_describe_generic(base, generic_params).parameters for base in getattr(cls, '__orig_bases__', [])):
            _params.update(item)

        return TypeDescriptor(
            cls,
            parameters=FrozenDict(_params),
            is_optional=is_optional,
            is_dataclass=True,
            is_typed_dict=False,
        )

    if hasattr(cls, '__origin__'):
        origin = cls.__origin__
        return _describe_parametrized(cls, generic_params, is_optional, is_typed_dict, origin)

    if isinstance(cls, UnionType):
        return _describe_parametrized(cls, generic_params, is_optional, is_typed_dict, Union)

    if isinstance(cls, type) and len(params) == 0 and not is_typed_dict:
        params = _get_default_generic_params(cls, params)

    if isinstance(cls, TypeVar) and cls.__constraints__:
        return _describe_generic(Union[cls.__constraints__], generic_params)

    return TypeDescriptor(
        cls,
        parameters=FrozenDict(params),
        is_optional=is_optional,
        is_dataclass=is_dataclass(cls),
        is_typed_dict=is_typed_dict,
    )


def _describe_parametrized(cls, generic_params, is_optional, is_typed_dict, origin):
    origin_is_dc = is_dataclass(origin)
    if origin_is_dc:
        params = _collect_type_vars(cls, generic_params)
    else:
        def describe_(arg):
            if type(arg) is TypeVar:
                if arg.__constraints__:
                    return _describe_generic(Union[arg.__constraints__], generic_params)
                return describe(Any, generic_params)
            return describe(arg, generic_params)
        params = dict(enumerate(map(describe_, getattr(cls, '__args__', []))))
    if isinstance(origin, type) and len(params) == 0:
        params = _get_default_generic_params(origin, params)
    descriptor = TypeDescriptor(
        origin,
        parameters=FrozenDict(params),
        is_optional=is_optional,
        is_dataclass=origin_is_dc,
        is_typed_dict=is_typed_dict,
    )
    return descriptor


def _collect_type_vars(alias: Any, generic_params: GenericParams) -> GenericParams:
    return dict(zip(alias.__origin__.__parameters__,
                    (describe(arg, generic_params) for arg in alias.__args__)))


class DescTypes:
    types: FrozenList[Type]

    def __init__(self, types: Iterable[Type]):
        super().__setattr__('types', FrozenList(types))

    @classmethod
    def scan(cls, desc: TypeDescriptor, *, known: List[TypeDescriptor]) -> 'DescTypes':
        if desc in known:
            return _empty_desc_types
        known.append(desc)
        dts = []  # type: List[DescTypes]
        for param in desc.parameters.values():
            dts.append(cls.scan(param, known=known))
        for child_desc in desc.fields.values():
            dts.append(cls.scan(child_desc, known=known))
        types = [type_ for dt in dts for type_ in dt.types]
        types.append(desc.cls)
        return cls(types)

    def __setattr__(self, key, value):
        raise AttributeError('Attempt to modify an immutable object')

    def __contains__(self, item):
        return item in self.types


_empty_desc_types = DescTypes({})


def scan_types(desc: TypeDescriptor) -> DescTypes:
    """Create a `DescTypes` object for the provided descriptor.

    `DescTypes` allow checks of the descriptor tree."""
    return DescTypes.scan(desc, known=[])


def _is_optional(cls: Type) -> bool:
    """Returns True if the provided type is `Optional`."""
    return (getattr(cls, '__origin__', None) == Union or isinstance(cls, UnionType)) \
        and len(cls.__args__) > 1 \
        and type(None) in set(cls.__args__)
