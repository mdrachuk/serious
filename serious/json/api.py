import collections
import json
from dataclasses import dataclass, field, is_dataclass
from typing import Optional, Tuple, TypeVar, Type, Generic, List, MutableMapping, Collection, Any

from serious.serialization import DataClassPlainDictSerializer
from serious.json.errors import UnexpectedJson

T = TypeVar('T')


@dataclass(frozen=True)
class Dumping:
    indent: Optional[int] = None
    encoder_options: dict = field(default_factory=dict)

    @classmethod
    def defaults(cls):
        return cls()


@dataclass(frozen=True)
class Loading:
    allow_missing: bool = False
    allow_unexpected: bool = False
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
        self._serializer = DataClassPlainDictSerializer(cls, self._load.allow_missing, self._load.allow_unexpected)

    def dump(self, o: T) -> str:
        _check_isinstance(o, self._cls)
        return self._dump_any(self._serializer.dump(o))

    def dump_all(self, items: Collection[T]) -> str:
        dict_items = [self._serializer.dump(_check_isinstance(o, self._cls)) for o in items]
        return self._dump_any(dict_items)

    def load(self, json_: str) -> T:
        data: MutableMapping = json.loads(json_, **self._load.decoder_options)
        self._check_that_loading_an_object(data)
        return self._from_dict(data)

    def load_all(self, json_: str) -> List[T]:
        data: Collection = json.loads(json_, **self._load.decoder_options)
        self._check_that_loading_a_list(data)
        return [self._from_dict(each) for each in data]

    def _dump_any(self, dict_items):
        return json.dumps(dict_items,
                          skipkeys=False,
                          ensure_ascii=False,
                          check_circular=True,
                          allow_nan=False,
                          indent=self._dump.indent,
                          separators=None,
                          default=None,
                          sort_keys=False,
                          **self._dump.encoder_options)

    def _check_that_loading_an_object(self, data):
        if not isinstance(data, collections.Mapping):
            if isinstance(data, collections.Collection):
                raise UnexpectedJson(f'Expecting a single object in JSON, got a collection instead. '
                                     f'Use #load_all(cls) instead of #load(cls) '
                                     f'to decode an array of {self._cls} dataclasses.')
            raise UnexpectedJson(f'Expecting a single {self._cls} object encoded in JSON.')

    def _check_that_loading_a_list(self, data: Any):
        if not isinstance(data, collections.Collection):
            raise UnexpectedJson(f'Expecting an array of {self._cls} objects encoded in JSON.')
        if isinstance(data, collections.Mapping):
            raise UnexpectedJson(f'Expecting an array of objects encoded in JSON, got a mapping instead.'
                                 f'Use #load(cls) instead of #load_all(cls) '
                                 f'to decode a single {self._cls} dataclasses.')

    def _from_dict(self, data: MutableMapping):
        return self._serializer.load(data)


def schema(cls: Type[T],
           dump: Dumping = Dumping.defaults(),
           load: Loading = Loading.defaults()) -> JsonSchema[T]:
    return JsonSchema(cls, dump, load)
