import collections
import json
from dataclasses import dataclass, field, is_dataclass, fields
from typing import Optional, Tuple, TypeVar, Type, Generic, List, Any, MutableMapping, Collection, Dict

from serious.core import M2JsonEncoder, _decode_dataclass, _override, _overrides, _as_dict_or_list
from serious.json.errors import UnexpectedJson

T = TypeVar('T')


@dataclass(frozen=True)
class Dumping:
    encoder: Type[json.JSONEncoder] = M2JsonEncoder
    indent: Optional[int] = None
    separators: Optional[Tuple[str, str]] = None
    encoder_options: dict = field(default_factory=dict)

    @classmethod
    def defaults(cls):
        return cls()


def _overriden_dict(obj: Any) -> Dict[str, Any]:
    """
    A re-implementation of `asdict` (from `dataclasses`) with overrides.
    """
    result = []
    for f in fields(obj):
        value = _as_dict_or_list(getattr(obj, f.name))
        result.append((f.name, value))
    return _override(dict(result), _overrides(obj), 'encoder')


@dataclass(frozen=True)
class Loading:
    infer_missing: bool = False
    decoder_options: dict = field(default_factory=dict)

    @classmethod
    def defaults(cls):
        return cls()


def _check_isinstance(value, cls):
    if not isinstance(value, cls):
        raise Exception(f'Got "{value}" when expecting a "{cls}" instance.')
    return value


class JsonSchema(Generic[T]):

    def __init__(self, cls: Type[T], dump: Dumping, load: Loading):
        if not is_dataclass(cls):
            raise Exception('Serious can only operate on dataclasses for now.')
        self._cls = cls
        self._dump = dump
        self._load = load

    def dump(self, o: T) -> str:
        _check_isinstance(o, self._cls)
        return self._dump_any(_overriden_dict(o))

    def dump_all(self, items: Collection[T]) -> str:
        dict_items = [_check_isinstance(_overriden_dict(o), self._cls) for o in items]
        return self._dump_any(dict_items)

    def _dump_any(self, dict_items):
        return json.dumps(dict_items,
                          cls=self._dump.encoder,
                          skipkeys=False,
                          ensure_ascii=False,
                          check_circular=True,
                          allow_nan=False,
                          indent=self._dump.indent,
                          separators=None,
                          default=None,
                          sort_keys=False,
                          **self._dump.encoder_options)

    def load(self, json_: str) -> T:
        data: MutableMapping = json.loads(json_, **self._load.decoder_options)
        if not isinstance(data, collections.Mapping):
            if isinstance(data, collections.Collection):
                raise UnexpectedJson(f'Expecting a single object in JSON, got a collection instead. '
                                     f'Use #load_all(cls) instead of #load(cls) '
                                     f'to decode an array of {self._cls} dataclasses.')
            raise UnexpectedJson(f'Expecting a single {self._cls} object encoded in JSON.')
        return self._from_dict(data)

    def load_all(self, json_: str) -> List[T]:
        data: Collection = json.loads(json_, **self._load.decoder_options)
        if not isinstance(data, collections.Collection):
            raise UnexpectedJson(f'Expecting an array of {self._cls} objects encoded in JSON.')
        if isinstance(data, collections.Mapping):
            raise UnexpectedJson(f'Expecting an array of objects encoded in JSON, got a mapping instead.'
                                 f'Use #load(cls) instead of #load_all(cls) '
                                 f'to decode a single {self._cls} dataclasses.')
        return [self._from_dict(each) for each in data]

    def _from_dict(self, data: MutableMapping):
        return _decode_dataclass(self._cls, data, self._load.infer_missing)


def schema(cls: Type[T],
           dump: Dumping = Dumping.defaults(),
           load: Loading = Loading.defaults()) -> JsonSchema[T]:
    return JsonSchema(cls, dump, load)
