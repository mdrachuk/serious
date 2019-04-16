import json
from typing import Callable, Optional, Tuple, TypeVar, Union, Type, Generic, List, Dict

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
    def __init__(self, cls: Type[T], format='json', infer_missing=False, **kwargs):
        self._cls = cls
        self._format = format
        self._infer_missing = infer_missing
        self._kwargs = kwargs

    def one(self, json_: str) -> T:
        kvs = json.loads(json_, **self._kwargs)
        return self._from_dict(kvs)

    def many(self, json_: str) -> List[T]:
        kvs = json.loads(json_, **self._kwargs)
        return [self._from_dict(each) for each in kvs]

    def _from_dict(self, data: Dict):
        return _decode_dataclass(self._cls, data, self._infer_missing)


def load(cls: Type[T], **kwargs) -> DataClassLoader[T]:
    return DataClassLoader(cls, **kwargs)
