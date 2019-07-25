from datetime import datetime, timezone
from typing import TypeVar, Generic, overload

KT = TypeVar('KT')  # Key type.
VT = TypeVar('VT')  # Value type.


class FrozenDict(dict, Generic[KT, VT]):
    """
    A dictionary which cannot be changed a la frozenset.

    Does not check for immutability of its members.

    Implementation from [PEP-351](https://www.python.org/dev/peps/pep-0351/).
    """

    def __hash__(self):
        hash_ = 0
        for key, value in self.items():
            hash_ ^= hash((key, value))
        return hash_

    def _immutable(self, *args, **kws):
        raise TypeError('A FrozenDict instance cannot be changed')

    __setitem__ = _immutable
    __delitem__ = _immutable
    clear = _immutable
    update = _immutable
    setdefault = _immutable
    pop = _immutable
    popitem = _immutable


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
