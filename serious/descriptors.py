from collections import ChainMap
from dataclasses import dataclass, fields, is_dataclass, replace
from typing import Type, Any, TypeVar, Generic, get_type_hints, Dict, Mapping, Collection

from serious._collections import FrozenDict, frozendict
from serious.utils import _is_optional

T = TypeVar('T')

FrozenGenericParams = FrozenDict[Any, 'TypeDescriptor']
GenericParams = Mapping[Any, 'TypeDescriptor']


@dataclass(frozen=True)
class TypeDescriptor(Generic[T]):
    _cls: Type[T]
    parameters: FrozenGenericParams
    is_optional: bool
    is_dataclass: bool

    @property
    def cls(self):  # Python fails when providing cls as a keyword parameter to dataclasses
        return self._cls

    def non_optional(self):
        return replace(self, is_optional=False)

    @property
    def fields(self) -> Collection['FieldDescriptor']:
        types = get_type_hints(self.cls)  # type: Dict[str, Type]
        descriptors = {name: self.describe(type_) for name, type_ in types.items()}
        return [FieldDescriptor(f.name, descriptors[f.name], f.metadata) for f in fields(self.cls)]

    def describe(self, type_: Type) -> 'TypeDescriptor':
        return describe(type_, self.parameters)


def describe(type_: Type[T], generic_params: GenericParams = None) -> TypeDescriptor[T]:
    generic_params = generic_params if generic_params is not None else {}
    param = generic_params.get(type_, None)
    if param is not None:
        return param
    return _unwrap_generic(type_, generic_params)


def _unwrap_generic(cls: Type, generic_params: GenericParams) -> TypeDescriptor:
    params: GenericParams = {}
    is_optional = _is_optional(cls)
    if is_optional:
        cls = cls.__args__[0]
    if hasattr(cls, '__orig_bases__') and is_dataclass(cls):
        params = dict(ChainMap(*(_unwrap_generic(base, generic_params).parameters for base in cls.__orig_bases__)))
        return TypeDescriptor(cls, frozendict(params), is_optional, is_dataclass=True)
    if hasattr(cls, '__origin__'):
        origin_is_dc = is_dataclass(cls.__origin__)
        if origin_is_dc:
            params = _collect_type_vars(cls, generic_params)
        else:
            describe_ = lambda arg: describe(Any if type(arg) is TypeVar else arg, generic_params)
            params = dict(enumerate(map(describe_, cls.__args__)))
        return TypeDescriptor(cls.__origin__, frozendict(params), is_optional, origin_is_dc)
    return TypeDescriptor(cls, frozendict(params), is_optional, is_dataclass(cls))


def _collect_type_vars(alias: Any, generic_params: GenericParams) -> GenericParams:
    return dict(zip(alias.__origin__.__parameters__,
                    (describe(arg, generic_params) for arg in alias.__args__)))


@dataclass(frozen=True)
class FieldDescriptor:
    """A descriptor of a dataclass field."""
    name: str
    type: TypeDescriptor
    metadata: Any
