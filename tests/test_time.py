from dataclasses import dataclass, field
from datetime import datetime, timezone

from serious.json import JsonSerializer


@dataclass
class DataclassWithDatetime:
    created_at: datetime


@dataclass
class DataclassWithIsoDatetime:
    created_at: datetime = field(
        metadata={'serious': {
            'dump': datetime.isoformat,
            'load': datetime.fromisoformat,
        }})


class TestTime:

    def setup_class(self):
        self.timestamp_schema = JsonSerializer(DataclassWithDatetime)
        self.iso_schema = JsonSerializer(DataclassWithIsoDatetime)

        dt = datetime(2018, 11, 17, 16, 55, 28, 456753, tzinfo=timezone.utc)
        tz = timezone.utc

        ts = dt.timestamp()
        self.dc_ts_json = f'{{"created_at": {ts}}}'
        self.dc_ts = DataclassWithDatetime(datetime.fromtimestamp(ts, tz=tz))

        iso = dt.isoformat()
        self.dc_iso_json = f'{{"created_at": "{iso}"}}'
        self.dc_iso = DataclassWithIsoDatetime(datetime.fromisoformat(iso))

    def test_datetime_decode(self):
        assert self.timestamp_schema.load(self.dc_ts_json) == self.dc_ts

    def test_datetime_encode(self):
        assert self.timestamp_schema.dump(self.dc_ts) == self.dc_ts_json

    def test_datetime_override_decode(self):
        assert self.iso_schema.load(self.dc_iso_json) == self.dc_iso

    def test_datetime_override_encode(self):
        assert self.iso_schema.dump(self.dc_iso) == self.dc_iso_json
