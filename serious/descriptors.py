from collections import ChainMap
from dataclasses import dataclass, fields, is_dataclass, replace
from typing import Type, Any, TypeVar, Generic, get_type_hints, Dict, Mapping, Collection, List, Union

from serious._collections import FrozenDict, frozendict

T = TypeVar('T')

FrozenGenericParams = FrozenDict[Any, 'TypeDescriptor']
GenericParams = Mapping[Any, 'TypeDescriptor']


@dataclass(frozen=True)
class TypeDescriptor(Generic[T]):
    _cls: Type[T]
    parameters: FrozenGenericParams
    is_optional: bool = False
    is_dataclass: bool = False

    @property
    def cls(self):  # Python fails when providing cls as a keyword parameter to dataclasses
        return self._cls

    def non_optional(self):
        return replace(self, is_optional=False)

    @property
    def fields(self) -> Collection['FieldDescriptor']:
        if not is_dataclass(self.cls):
            return []
        types = get_type_hints(self.cls)  # type: Dict[str, Type]
        descriptors = {name: self.describe(type_) for name, type_ in types.items()}
        return [
            FieldDescriptor(name=f.name, type=descriptors[f.name], metadata=f.metadata)
            for f in fields(self.cls)
        ]

    def describe(self, type_: Type) -> 'TypeDescriptor':
        return describe(type_, self.parameters)


def describe(type_: Type[T], generic_params: GenericParams = None) -> TypeDescriptor[T]:
    generic_params = generic_params if generic_params is not None else {}
    param = generic_params.get(type_, None)
    if param is not None:
        return param
    return _unwrap_generic(type_, generic_params)


_any_type_desc = TypeDescriptor(Any, frozendict())  # type: ignore
_ellipses_type_desc = TypeDescriptor(Ellipsis, frozendict())  # type: ignore
_generic_params = {
    list: {0: _any_type_desc},
    set: {0: _any_type_desc},
    frozenset: {0: _any_type_desc},
    tuple: {0: _any_type_desc, 1: _ellipses_type_desc},
    dict: {0: _any_type_desc, 1: _any_type_desc},
}  # type: Dict[Type, Dict[int, TypeDescriptor]]


def _get_default_generic_params(cls: Type, params: GenericParams) -> GenericParams:
    for generic, default_params in _generic_params.items():
        if issubclass(cls, generic):
            return default_params
    return params


def _unwrap_generic(cls: Type, generic_params: GenericParams) -> TypeDescriptor:
    params: GenericParams = {}
    is_optional = _is_optional(cls)
    if is_optional:
        cls = cls.__args__[0]
    if hasattr(cls, '__orig_bases__') and is_dataclass(cls):
        params = dict(ChainMap(*(_unwrap_generic(base, generic_params).parameters for base in cls.__orig_bases__)))
        return TypeDescriptor(
            _cls=cls,
            parameters=frozendict(params),
            is_optional=is_optional,
            is_dataclass=True
        )
    if hasattr(cls, '__origin__'):
        origin_is_dc = is_dataclass(cls.__origin__)
        if origin_is_dc:
            params = _collect_type_vars(cls, generic_params)
        else:
            describe_ = lambda arg: describe(Any if type(arg) is TypeVar else arg, generic_params)
            params = dict(enumerate(map(describe_, cls.__args__)))
        return TypeDescriptor(
            _cls=cls.__origin__,
            parameters=frozendict(params),
            is_optional=is_optional,
            is_dataclass=origin_is_dc
        )
    if isinstance(cls, type) and len(params) == 0:
        params = _get_default_generic_params(cls, params)
    return TypeDescriptor(
        _cls=cls,
        parameters=frozendict(params),
        is_optional=is_optional,
        is_dataclass=is_dataclass(cls)
    )


def _collect_type_vars(alias: Any, generic_params: GenericParams) -> GenericParams:
    return dict(zip(alias.__origin__.__parameters__,
                    (describe(arg, generic_params) for arg in alias.__args__)))


@dataclass(frozen=True)
class FieldDescriptor:
    """A descriptor of a dataclass field."""
    name: str
    type: TypeDescriptor
    metadata: Any


def _scan_types(desc: TypeDescriptor, _known_descriptors: List[TypeDescriptor] = None) -> Collection[Type]:
    if _known_descriptors is None:
        _known_descriptors = [desc]
    elif desc in _known_descriptors:
        return []
    else:
        _known_descriptors.append(desc)
    types = []  # type: List[Type]
    for param in desc.parameters.values():
        types.extend(_scan_types(param, _known_descriptors))
    for field in desc.fields:
        types.extend(_scan_types(field.type, _known_descriptors))
    types.append(desc.cls)
    return types


def _contains_any(desc: TypeDescriptor) -> bool:
    all_types = _scan_types(desc)
    return Any in all_types


def _is_optional(cls: Type) -> bool:
    """Returns True if the provided type is Optional."""
    return hasattr(cls, '__origin__') \
           and cls.__origin__ == Union \
           and len(cls.__args__) == 2 \
           and cls.__args__[1] == type(None)