"""Serializable types provided by serious.

`serious.types` module lists a number of types useful for as part of serious modules:
- Timestamp — an alternative to datetime, that is serialized to a float ms value
- Email — a Tiny Type made out of string, which is checked to match the format
- FrozenList and FrozenDict — immutable alternatives for standard collections
"""

from __future__ import annotations

__all__ = ['Timestamp', 'Email', 'FrozenList', 'FrozenDict']

import re
from datetime import datetime, timezone
from typing import TypeVar, Generic, overload, Optional, Mapping, Iterator

from .errors import ValidationError

KT = TypeVar('KT')  # Key type.
VT = TypeVar('VT')  # Value type.


class FrozenDict(Mapping[KT, VT]):
    """
    A dictionary which cannot be changed a la frozenset.

    Does not check for immutability of its members.
    """

    def __init__(self, mapping: Optional[Mapping[KT, VT]] = None, **kwargs: Mapping[KT, VT]) -> None:
        if mapping is not None:
            self.__internal_mapping__ = dict(mapping)
        else:
            self.__internal_mapping__ = dict(**kwargs)

    def __getitem__(self, __k: KT) -> VT:
        return self.__internal_mapping__[__k]

    def __len__(self) -> int:
        return len(self.__internal_mapping__)

    def __iter__(self) -> Iterator[KT]:
        return iter(self.__internal_mapping__)

    def __hash__(self):
        hash_ = 0
        for key, value in self.items():
            hash_ ^= hash((key, value))
        return hash_

    def __or__(self, other: Mapping) -> FrozenDict:
        if hasattr(other, 'items'):
            result = dict(self)
            result.update(other)
            return FrozenDict(result)
        raise TypeError(f'Cannot merge {type(self)} with {type(other)}')

    def __repr__(self):
        return f'FrozenDict({self.__internal_mapping__})'


class FrozenList(tuple, Generic[VT]):
    """A list that cannot be changed. `FrozenList[VT]` is equal to saying `Tuple[VT, ...]`."""
    pass


class Timestamp:
    """An immutable(frozen) UTC timestamp.

    Constructor accepts a single arguments. One of:
    - datetime object
    - ISO 8601 formatted string
    - number of seconds since UNIX epoch in int or float
    - a Timestamp object to create its copy

    Supports comparison with another Timestamp objects.
    """

    value: float

    @overload
    def __init__(self, dt: datetime):
        """Creates a timestamp matching the value of a datetime instance."""
        pass

    @overload
    def __init__(self, iso_string: str):
        """Creates a timestamp from a provided ISO 8601 formatted string."""
        pass

    @overload
    def __init__(self, timestamp: int):
        """Creates a timestamp with provided number of seconds since UNIX epoch (January 1st, 1970)."""
        pass

    @overload
    def __init__(self, timestamp: float):
        """Creates a timestamp with provided number of seconds since UNIX epoch (January 1st, 1970)."""
        pass

    @overload
    def __init__(self, timestamp: 'Timestamp'):
        """Creates a copy of a timestamp."""
        pass

    def __init__(self, value):
        if isinstance(value, Timestamp):
            super().__setattr__('value', value.value)
        elif isinstance(value, datetime):
            super().__setattr__('value', self._datetime_value(value))
        elif isinstance(value, str):
            dt = datetime.fromisoformat(value)
            super().__setattr__('value', self._datetime_value(dt))
        elif isinstance(value, int):
            super().__setattr__('value', float(value))
        elif isinstance(value, float):
            super().__setattr__('value', value)
        else:
            raise ValueError(f'Timestamp cannot be created from "{value}"')

    @staticmethod
    def _datetime_value(value):
        offset = value.utcoffset()
        if offset:
            value = value - offset
        return value.timestamp()

    def as_datetime(self) -> datetime:
        """Constructs a datetime object with the timestamp value."""
        return datetime.fromtimestamp(self.value, tz=timezone.utc)

    def as_iso(self):
        """ISO 8601 representation of a timestamp. Same as str(timestamp(value))"""
        return datetime.fromtimestamp(self.value, tz=timezone.utc).isoformat()

    def __setattr__(self, name, value):
        """Restricts mutation of object value"""
        raise AttributeError('Cannot change timestamp. Timestamp objects are immutable.')

    def __eq__(self, other: object):
        """Overrides the default implementation"""
        if not isinstance(other, Timestamp):
            raise NotImplementedError('Cannot compare Timestamp to anything other than Timestamp.')
        return self.value == other.value

    def __lt__(self, other: 'Timestamp'):
        if not isinstance(other, Timestamp):
            raise NotImplementedError('Cannot compare Timestamp to anything other than Timestamp.')
        return self.value < other.value

    def __le__(self, other: 'Timestamp'):
        if not isinstance(other, Timestamp):
            raise NotImplementedError('Cannot compare Timestamp to anything other than Timestamp.')
        return self.value <= other.value

    def __ge__(self, other: 'Timestamp'):
        if not isinstance(other, Timestamp):
            raise NotImplementedError('Cannot compare Timestamp to anything other than Timestamp.')
        return self.value >= other.value

    def __gt__(self, other: 'Timestamp'):
        if not isinstance(other, Timestamp):
            raise NotImplementedError('Cannot compare Timestamp to anything other than Timestamp.')
        return self.value > other.value

    def __str__(self):
        """ISO 8601 representation of a timestamp."""
        return self.as_iso()

    def __repr__(self):
        """An unambiguous representation of an object."""
        iso_str = self.as_iso()
        return f'<{self.__class__.__name__} {iso_str} ({self.value})>'


_email_regex = re.compile(r'^\w(\.|\w|-)*\+?(\.|\w|-)*@\w(\.|\w|-)*(\.\w+)$',
                          re.IGNORECASE | re.UNICODE)


class Email(str):
    """A regular email address. Email parts can be accessed via properties: `<username>+<label>@<domain>`."""

    def __new__(cls, content: str):
        return super().__new__(cls, content.lower())  # type: ignore # __new__ is a staticmethod

    @property
    def username(self) -> str:
        return self.split('@')[0].split('+')[0]

    @property
    def label(self) -> Optional[str]:
        user_and_label = self.split('@')[0].split('+')
        if len(user_and_label) == 1:
            return None
        return user_and_label[1]

    @property
    def domain(self) -> str:
        return self.split('@')[1]

    def __validate__(self):
        if _email_regex.match(self) is None:
            raise ValidationError('Invalid email format')

    def __repr__(self):
        return f'<{self.__class__.__name__} {str(self)}>'
