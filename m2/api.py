import json
from dataclasses import dataclass, field
from typing import Optional, Tuple, TypeVar, Type, Generic, Mapping, List, Any

from m2.core import M2JsonEncoder, _as_dict_or_list, _decode_dataclass

T = TypeVar('T')


@dataclass(frozen=True)
class DumpOptions:
    encoder: json.JSONEncoder = M2JsonEncoder
    indent: Optional[int] = None
    separators: Optional[Tuple[str, str]] = None
    encoder_options: dict = field(default_factory=dict)


def asjson(o: Any, options: DumpOptions = DumpOptions()) -> str:
    """
    Dumps the provided datataclass, list or mapping object to a JSON string.
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


class DataClassLoader(Generic[T]):
    def __init__(self, cls: Type[T], infer_missing=False, **kwargs):
        self._cls = cls
        self._infer_missing = infer_missing
        self._kwargs = kwargs

    def from_(self, json_: str) -> T:
        data = json.loads(json_, **self._kwargs)
        return self._from_dict(data)

    def _from_dict(self, data: Mapping):
        return _decode_dataclass(self._cls, data, self._infer_missing)


class DataClassListLoader(DataClassLoader[T]):
    def from_(self, json_: str) -> List[T]:
        data = json.loads(json_, **self._kwargs)
        return [self._from_dict(each) for each in data]


def load(cls: Type[T], **kwargs) -> DataClassLoader[T]:
    return DataClassLoader(cls, **kwargs)


def load_all(cls: Type[T], **kwargs) -> DataClassListLoader[T]:
    return DataClassListLoader(cls, **kwargs)
