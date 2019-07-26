from dataclasses import dataclass, field
from datetime import datetime, timezone

import pytest

from serious import JsonSchema
from serious.errors import InvalidFieldMetadata


@dataclass
class CustomDateTime:
    timestamp: datetime = field(
        metadata={'serious': {
            'dump': lambda x, ctx: x.timestamp(),
            'load': lambda x, ctx: datetime.fromtimestamp(x, timezone.utc),
        }})


@dataclass
class MissingLoad:
    timestamp: datetime = field(metadata={'serious': {'dump': lambda x: x.timestamp()}})


@dataclass
class MissingDump:
    timestamp: datetime = field(metadata={'serious': {'load': lambda x: datetime.fromtimestamp(x, timezone.utc)}})


@dataclass
class DefaultSerializer:
    timestamp: datetime = field(metadata={'serious': {}})


class TestDumpAndLoadCheck:

    def test_load(self):
        with pytest.raises(InvalidFieldMetadata):
            JsonSchema(MissingLoad)

    def test_dump(self):
        with pytest.raises(InvalidFieldMetadata):
            JsonSchema(MissingDump)

    def test_valid(self):
        assert JsonSchema(DefaultSerializer)
        assert JsonSchema(CustomDateTime)


class TestCustomDatetime:

    def setup_class(self):
        self.schema = JsonSchema(CustomDateTime)
        dt = datetime(2018, 11, 17, 16, 55, 28, 456753, tzinfo=timezone.utc)
        ts = dt.timestamp()
        self.json = f'{{"timestamp": {ts}}}'
        self.dataclass = CustomDateTime(timestamp=datetime.fromtimestamp(ts, tz=timezone.utc))

    def test_load(self):
        assert self.schema.load(self.json) == self.dataclass

    def test_dump(self):
        assert self.schema.dump(self.dataclass) == self.json
