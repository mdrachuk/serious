import json
from typing import Callable, Optional, Tuple, TypeVar, Union, Type, Generic, Mapping, List

from m2.core import _ExtendedEncoder, _asdict, _decode_dataclass

T = TypeVar('T')


def asjson(o, *,
           skipkeys: bool = False,
           ensure_ascii: bool = True,
           check_circular: bool = True,
           allow_nan: bool = True,
           indent: Optional[Union[int, str]] = None,
           separators: Tuple[str, str] = None,
           default: Callable = None,
           sort_keys: bool = False,
           **kw) -> str:
    return json.dumps(_asdict(o),
                      cls=_ExtendedEncoder,
                      skipkeys=skipkeys,
                      ensure_ascii=ensure_ascii,
                      check_circular=check_circular,
                      allow_nan=allow_nan,
                      indent=indent,
                      separators=separators,
                      default=default,
                      sort_keys=sort_keys,
                      **kw)


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
