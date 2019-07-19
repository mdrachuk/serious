from dataclasses import dataclass, field
from datetime import datetime, timezone, time, date

from serious.json import JsonSchema
from serious.types import Timestamp, timestamp


@dataclass
class Post:
    created_at: datetime


class TestDefaultDatetime:

    def setup_class(self):
        self.schema = JsonSchema(Post)
        dt = datetime(2018, 11, 17, 16, 55, 28, 456753, tzinfo=timezone.utc)
        iso = dt.isoformat()
        self.json = f'{{"created_at": "{iso}"}}'
        self.dataclass = Post(datetime.fromisoformat(iso))

    def test_load(self):
        assert self.schema.load(self.json) == self.dataclass

    def test_dump(self):
        assert self.schema.dump(self.dataclass) == self.json


@dataclass
class CustomDateTime:
    timestamp: datetime = field(
        metadata={'serious': {
            'dump': lambda x: x.timestamp(),
            'load': lambda x: datetime.fromtimestamp(x, timezone.utc),
        }})


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


@dataclass
class TimestampDatetime:
    value: Timestamp


class TestTimestamp:

    def setup_class(self):
        self.schema = JsonSchema(TimestampDatetime)
        dt = datetime(2018, 11, 17, 16, 55, 28, 456753, tzinfo=timezone.utc)
        ts = dt.timestamp()
        self.json = f'{{"value": {ts}}}'
        self.dataclass = TimestampDatetime(timestamp(dt))

    def test_load(self):
        assert self.schema.load(self.json) == self.dataclass

    def test_dump(self):
        assert self.schema.dump(self.dataclass) == self.json


@dataclass
class Event:
    what: str
    when: date


class TestDate:

    def setup_class(self):
        self.schema = JsonSchema(Event)
        self.json = f'{{"what": "Nobel Prize", "when": "1922-09-09"}}'
        self.dataclass = Event("Nobel Prize", date(1922, 9, 9))

    def test_load(self):
        assert self.schema.load(self.json) == self.dataclass

    def test_dump(self):
        assert self.schema.dump(self.dataclass) == self.json


@dataclass
class Alarm:
    at: time
    enabled: bool


class TestTime:

    def setup_class(self):
        self.schema = JsonSchema(Alarm)
        self.json = f'{{"at": "07:00:00", "enabled": true}}'
        self.dataclass = Alarm(time(7, 0, 0), enabled=True)

    def test_load(self):
        assert self.schema.load(self.json) == self.dataclass

    def test_dump(self):
        assert self.schema.dump(self.dataclass) == self.json
