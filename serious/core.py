import copy
import json
import warnings
from dataclasses import (MISSING, _is_dataclass_instance,  # type: ignore # internal function function
                         fields, is_dataclass, dataclass, Field)
from datetime import datetime, timezone
from enum import Enum
from typing import (Collection, Mapping, Union, get_type_hints,
                    Type, Any, Dict, Iterator, NamedTuple, Callable,
                    MutableMapping)
from uuid import UUID

from serious.utils import (_get_constructor, _is_collection, _is_mapping, _is_optional,
                           _isinstance_safe, _issubclass_safe)

serious = 'serious'

DataClassType = Type[Any]
JSON = Union[dict, list, str, int, float, bool, None]


class M2JsonEncoder(json.JSONEncoder):
    def default(self, o) -> JSON:
        if _isinstance_safe(o, Collection):
            if _isinstance_safe(o, Mapping):
                return dict(o)
            else:
                return list(o)
        elif _isinstance_safe(o, datetime):
            return o.timestamp()
        elif _isinstance_safe(o, UUID):
            return str(o)
        elif _isinstance_safe(o, Enum):
            return o.value
        return super().default(o)


class FieldOverride(NamedTuple):
    dump: Callable[[], str]
    load: Callable[[str], Any]


def _overrides(dc: Union[DataClassType, Any]) -> Dict[str, FieldOverride]:
    overrides = {}
    for field in fields(dc):
        # if the field has serious metadata, we cons a FieldOverride
        # so there's a distinction between FieldOverride with all Nones
        # and field that just doesn't appear in overrides
        if field.metadata is not None and serious in field.metadata:
            metadata = field.metadata[serious]
            overrides[field.name] = FieldOverride(**{key: value for key, value in metadata.items()})
    return overrides


def _override(data: Mapping, overrides: Mapping, override_name: str):
    override_kvs = {}
    for k, v in data.items():
        if k in overrides and getattr(overrides[k], override_name) is not None:
            override_kvs[k] = getattr(overrides[k], override_name)(v)
        else:
            override_kvs[k] = v
    return override_kvs


@dataclass
class _Attr:
    of: DataClassType
    name: str
    type: Type
    value: Any


def _attrs(cls: DataClassType, data: Mapping) -> Iterator[_Attr]:
    types = get_type_hints(cls)
    return (_Attr(cls, field.name, types[field.name], value=data[field.name]) for field in fields(cls))


def _decode_dataclass(cls: DataClassType, data: MutableMapping, infer_missing: bool):
    overrides = _overrides(cls)
    data = {} if data is None and infer_missing else data
    for field in _fields_missing_from(data, cls):
        if field.default is not MISSING:
            data[field.name] = field.default
        elif field.default_factory is not MISSING:  # type: ignore # method is supplied to constructor -> missing self
            data[field.name] = field.default_factory()  # type: ignore
        elif infer_missing:
            data[field.name] = None

    init_kwargs = {}
    for attr in _attrs(cls, data):
        init_kwargs[attr.name] = _decode_attr_value(attr, infer_missing, overrides)
    return cls(**init_kwargs)


def _fields_missing_from(data: Mapping, cls: DataClassType) -> Iterator[Field]:
    return filter(lambda field: field.name not in data, fields(cls))


def _decode_attr_value(attr: _Attr, infer_missing: bool, overrides: Dict[str, FieldOverride]) -> Any:
    if not _is_optional(attr.type) and attr.value is None:
        warning = f'value of non-optional type {attr.name} detected when decoding {attr.of.__name__}'
        if infer_missing:
            warnings.warn(
                f"Missing {warning} and was defaulted to None by "
                f"infer_missing=True. "
                f"Set infer_missing=False (the default) to prevent this "
                f"behavior.", RuntimeWarning)
        else:
            warnings.warn(f"`NoneType` object {warning}.", RuntimeWarning)
        return attr.value
    elif attr.name in overrides and overrides[attr.name].load is not None:
        return overrides[attr.name].load(attr.value)
    elif is_dataclass(attr.type):
        value = _decode_dataclass(attr.type, attr.value, infer_missing)
        return value
    elif _is_supported_generic(attr.type) and attr.type != str:
        return _decode_generic(attr.type, attr.value, infer_missing)
    elif _issubclass_safe(attr.type, datetime):
        tz = datetime.now(timezone.utc).astimezone().tzinfo
        dt = datetime.fromtimestamp(attr.value, tz=tz)
        return dt
    elif _issubclass_safe(attr.type, UUID) and not isinstance(attr.value, UUID):
        return UUID(attr.value)
    return attr.value


def _is_supported_generic(type_: Type):
    not_str = not _issubclass_safe(type_, str)
    is_enum = _issubclass_safe(type_, Enum)
    return (not_str and _is_collection(type_)) or _is_optional(type_) or is_enum


def _decode_generic(type_: Type, value: Any, infer_missing: bool) -> Any:
    if value is None:
        res = value
    elif _issubclass_safe(type_, Enum):
        # Convert to an Enum using the type as a constructor. Assumes a direct match is found.
        res = type_(value)
    elif _is_collection(type_):
        if _is_mapping(type_):
            k_type, v_type = type_.__args__
            # a mapping type has `.keys()` and `.values()` (see collections.abc)
            ks = _decode_dict_keys(k_type, value.keys(), infer_missing)
            vs = _decode_items(v_type, value.values(), infer_missing)
            xs = zip(ks, vs)
        else:
            xs = _decode_items(type_.__args__[0], value, infer_missing)

        # get the constructor if using corresponding generic type in `typing`
        # otherwise fallback on constructing using type_ itself
        try:
            res = _get_constructor(type_)(xs)
        except TypeError:
            res = type_(xs)
    else:  # Optional
        type_arg = type_.__args__[0]
        if is_dataclass(type_arg) or is_dataclass(value):
            res = _decode_dataclass(type_arg, value, infer_missing)
        elif _is_supported_generic(type_arg):
            res = _decode_generic(type_arg, value, infer_missing)
        else:
            res = value
    return res


def _decode_dict_keys(key_type: Type, xs: Any, infer_missing: bool):
    """
    Because JSON object keys must be strings, we need the extra step of decoding
    them back into the user's chosen python type
    """
    # Handle NoneType keys. It's weird to type a Dict as NoneType keys but it's valid.
    key_type = (lambda x: x) if key_type is type(None) else key_type  # type: ignore # a constructor is replaced by noop
    return map(key_type, _decode_items(key_type, xs, infer_missing))


def _decode_items(type_arg: Type, xs: Any, infer_missing: bool):
    """
    This is a tricky situation where we need to check both the annotated
    type info (which is usually a type from `typing`) and check the
    value's type directly using `type()`.

    If the type_arg is a generic we can use the annotated type, but if the
    type_arg is a typevar we need to extract the reified type information
    hence the check of `is_dataclass(vs)`
    """
    if is_dataclass(type_arg) or is_dataclass(xs):
        items = (_decode_dataclass(type_arg, x, infer_missing) for x in xs)
    elif _is_supported_generic(type_arg):
        items = (_decode_generic(type_arg, x, infer_missing) for x in xs)
    else:
        items = xs
    return items


def _as_dict_or_list(obj: Any) -> JSON:
    """
    A re-implementation of `asdict` (based on the original in the `dataclasses`
    source) to support arbitrary Collection and Mapping types.
    """
    if _is_dataclass_instance(obj):
        return _overriden_dict(obj)
    elif isinstance(obj, Mapping):
        return dict((_as_dict_or_list(k), _as_dict_or_list(v)) for k, v in obj.items())
    elif isinstance(obj, Collection) and not isinstance(obj, str):
        return list(_as_dict_or_list(v) for v in obj)
    else:
        return copy.deepcopy(obj)


def _overriden_dict(obj: Any) -> Dict[str, Any]:
    """
    A re-implementation of `asdict` (from `dataclasses`) with overrides.
    """
    result = []
    for f in fields(obj):
        value = _as_dict_or_list(getattr(obj, f.name))
        result.append((f.name, value))
    return _override(dict(result), _overrides(obj), 'dump')
