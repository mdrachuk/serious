import collections
import json
from dataclasses import dataclass, field
from typing import Optional, Tuple, TypeVar, Type, Generic, List, Any, MutableMapping, Collection

from m2.core import M2JsonEncoder, _as_dict_or_list, _decode_dataclass

T = TypeVar('T')
X = TypeVar('X')
Y = TypeVar('Y')


@dataclass(frozen=True)
class DumpOptions:
    encoder: Type[json.JSONEncoder] = M2JsonEncoder
    indent: Optional[int] = None
    separators: Optional[Tuple[str, str]] = None
    encoder_options: dict = field(default_factory=dict)


def asjson(o: Any, options: DumpOptions = DumpOptions()) -> str:
    """
    Dumps the provided datataclass, list or mapping to a JSON string.
    """
    return json.dumps(_as_dict_or_list(o),
                      cls=options.encoder,
                      skipkeys=False,
                      ensure_ascii=False,
                      check_circular=True,
                      allow_nan=False,
                      indent=options.indent,
                      separators=None,
                      default=None,
                      sort_keys=False,
                      **options.encoder_options)


class UnexpectedJson(Exception):
    def __init__(self, extra_message=None):
        super(UnexpectedJson, self).__init__(f'Unexpected JSON document. {extra_message}')


class JsonObjectLoader(Generic[X, Y]):
    """
    Loads a single dataclass object from JSON string.
    Raises an error if the string is not a single encoded object of the provided class.
    """

    def __init__(self, cls: Type[X], infer_missing=False, **kwargs):
        self._cls = cls
        self._infer_missing = infer_missing
        self._kwargs = kwargs

    def from_(self, json_: str) -> Y:
        data: MutableMapping = json.loads(json_, **self._kwargs)
        if not isinstance(data, collections.Mapping):
            if isinstance(data, collections.Collection):
                raise UnexpectedJson(f'Expecting a single object in JSON, got a collection instead. '
                                     f'Use m2.load_all(cls) instead of m2.load(cls) '
                                     f'to decode an array of {self._cls} dataclasses.')
            raise UnexpectedJson(f'Expecting a single {self._cls} object encoded in JSON.')
        return self._from_dict(data)

    def _from_dict(self, data: MutableMapping):
        return _decode_dataclass(self._cls, data, self._infer_missing)


class JsonArrayLoader(JsonObjectLoader[X, List[X]]):
    """
    Loads a list of dataclass objects from JSON string.
    Raises an error if the string is not a single encoded object of the provided class.
    """

    def from_(self, json_: str) -> List[X]:
        data: Collection = json.loads(json_, **self._kwargs)
        if not isinstance(data, collections.Collection):
            raise UnexpectedJson(f'Expecting an array of {self._cls} objects encoded in JSON.')
        if isinstance(data, collections.Mapping):
            raise UnexpectedJson(f'Expecting an array of objects encoded in JSON, got a mapping instead.'
                                 f'Use m2.load(cls) instead of m2.load_all(cls) '
                                 f'to decode a single {self._cls} dataclasses.')
        return [self._from_dict(each) for each in data]


def load(cls: Type[T], **kwargs) -> JsonObjectLoader[T, T]:
    return JsonObjectLoader(cls, **kwargs)


def load_all(cls: Type[T], **kwargs) -> JsonArrayLoader[T]:
    return JsonArrayLoader(cls, **kwargs)
