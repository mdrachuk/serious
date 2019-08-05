from dataclasses import dataclass
from datetime import datetime, timezone, time, date

from serious import JsonModel, Timestamp


@dataclass
class Post:
    created_at: datetime


class TestDefaultDatetime:

    def setup_class(self):
        self.model = JsonModel(Post)
        dt = datetime(2018, 11, 17, 16, 55, 28, 456753, tzinfo=timezone.utc)
        iso = dt.isoformat()
        self.json = f'{{"created_at": "{iso}"}}'
        self.dataclass = Post(datetime.fromisoformat(iso))

    def test_load(self):
        assert self.model.load(self.json) == self.dataclass

    def test_dump(self):
        assert self.model.dump(self.dataclass) == self.json


@dataclass
class TimestampDatetime:
    value: Timestamp


class TestTimestamp:

    def setup_class(self):
        self.model = JsonModel(TimestampDatetime)
        dt = datetime(2018, 11, 17, 16, 55, 28, 456753, tzinfo=timezone.utc)
        ts = dt.timestamp()
        self.json = f'{{"value": {ts}}}'
        self.dataclass = TimestampDatetime(Timestamp(dt))

    def test_load(self):
        assert self.model.load(self.json) == self.dataclass

    def test_dump(self):
        assert self.model.dump(self.dataclass) == self.json


@dataclass
class Event:
    what: str
    when: date


class TestDate:

    def setup_class(self):
        self.model = JsonModel(Event)
        self.json = f'{{"what": "Nobel Prize", "when": "1922-09-09"}}'
        self.dataclass = Event("Nobel Prize", date(1922, 9, 9))

    def test_load(self):
        assert self.model.load(self.json) == self.dataclass

    def test_dump(self):
        assert self.model.dump(self.dataclass) == self.json


@dataclass
class Alarm:
    at: time
    enabled: bool


class TestTime:

    def setup_class(self):
        self.model = JsonModel(Alarm)
        self.json = f'{{"at": "07:00:00", "enabled": true}}'
        self.dataclass = Alarm(time(7, 0, 0), enabled=True)

    def test_load(self):
        assert self.model.load(self.json) == self.dataclass

    def test_dump(self):
        assert self.model.dump(self.dataclass) == self.json
