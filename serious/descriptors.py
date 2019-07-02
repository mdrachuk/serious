from collections import ChainMap, namedtuple
from dataclasses import dataclass, fields, is_dataclass, replace
from typing import Type, Any, TypeVar, Generic, get_type_hints, Dict, Mapping, Union

from serious._collections import FrozenDict, frozendict
from serious.preconditions import _check_is_dataclass

T = TypeVar('T')

FrozenGenericParams = FrozenDict[Any, 'TypeDescriptor']
GenericParams = Mapping[Any, 'TypeDescriptor']


@dataclass(frozen=True)
class TypeDescriptor(Generic[T]):
    _cls: Type[T]
    generic_params: FrozenGenericParams
    is_optional: bool

    @property
    def cls(self):  # Python fails when providing cls as a keyword parameter to dataclasses
        return self._cls

    def non_optional(self):
        return replace(self, is_optional=False)


@dataclass(frozen=True)
class DataclassDescriptor(TypeDescriptor[T]):
    """A descriptor of a dataclass."""

    @classmethod
    def of(cls, type_: Type[T]) -> 'DataclassDescriptor[T]':
        """A factory creating dataclass descriptors."""
        type_, params, is_optional = unwrap_generic(type_, {})
        _check_is_dataclass(type_, 'Serious can only operate on dataclasses.')
        return cls(type_, frozendict(params), is_optional)

    @property
    def fields(self) -> Mapping[str, 'FieldDescriptor']:
        types = get_type_hints(self.cls)  # type: Dict[str, Type]
        descriptors = {name: self.describe(type_) for name, type_ in types.items()}
        return {f.name: FieldDescriptor(f.name, descriptors[f.name], f.metadata) for f in fields(self.cls)}

    def describe(self, type_: Type) -> TypeDescriptor:
        return describe(type_, self.generic_params)


def describe(type_: Type, generic_params: GenericParams) -> TypeDescriptor:
    as_param = generic_params.get(type_, None)
    if as_param is not None:
        cls, params, is_optional = as_param.cls, as_param.generic_params, as_param.is_optional
    else:
        cls, params, is_optional = unwrap_generic(type_, generic_params)
    if is_dataclass(cls):
        params = frozendict({**generic_params, **params})
        return DataclassDescriptor(cls, params, is_optional)
    return TypeDescriptor(cls, frozendict(params), is_optional)


Unwrapped = namedtuple('Unwrapped', ['type', 'params', 'is_optional'])


def unwrap_generic(cls: Type, generic_params: GenericParams) -> Unwrapped:
    params: GenericParams = {}
    is_optional = _is_optional(cls)
    if is_optional:
        cls = cls.__args__[0]
    if hasattr(cls, '__orig_bases__') and is_dataclass(cls):
        params = dict(ChainMap(*(unwrap_generic(base, generic_params)[1] for base in cls.__orig_bases__)))
        return Unwrapped(cls, params, is_optional)
    if hasattr(cls, '__origin__'):
        if is_dataclass(cls.__origin__):
            params = _collect_type_vars(cls, generic_params)
        else:
            describe_ = lambda arg: describe(Any if type(arg) is TypeVar else arg, generic_params)
            params = dict(enumerate(map(describe_, cls.__args__)))
        return Unwrapped(cls.__origin__, params, is_optional)
    return Unwrapped(cls, params, is_optional)


def _collect_type_vars(alias: Any, generic_params: GenericParams) -> GenericParams:
    return dict(zip(alias.__origin__.__parameters__,
                    (describe(arg, generic_params) for arg in alias.__args__)))


def _is_optional(cls: Type) -> bool:
    return hasattr(cls, '__origin__') \
           and cls.__origin__ == Union \
           and len(cls.__args__) == 2 \
           and cls.__args__[1] == type(None)


@dataclass(frozen=True)
class FieldDescriptor:
    """A descriptor of a dataclass field."""
    name: str
    type: TypeDescriptor
    metadata: Any
