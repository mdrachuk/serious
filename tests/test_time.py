from dataclasses import dataclass, field
from datetime import datetime, timezone

from serious.json import json_schema


@dataclass
class DataClassWithDatetime:
    created_at: datetime


@dataclass
class DataClassWithIsoDatetime:
    created_at: datetime = field(
        metadata={'serious': {
            'dump': datetime.isoformat,
            'load': datetime.fromisoformat,
        }})


timestamp_schema = json_schema(DataClassWithDatetime)
iso_schema = json_schema(DataClassWithIsoDatetime)


class TestTime:
    dt = datetime(2018, 11, 17, 16, 55, 28, 456753, tzinfo=timezone.utc)
    tz = timezone.utc

    ts = dt.timestamp()
    dc_ts_json = f'{{"created_at": {ts}}}'
    dc_ts = DataClassWithDatetime(datetime.fromtimestamp(ts, tz=tz))

    iso = dt.isoformat()
    dc_iso_json = f'{{"created_at": "{iso}"}}'
    dc_iso = DataClassWithIsoDatetime(datetime.fromisoformat(iso))

    def test_datetime_encode(self):
        assert timestamp_schema.dump(self.dc_ts) == self.dc_ts_json

    def test_datetime_decode(self):
        assert timestamp_schema.load(self.dc_ts_json) == self.dc_ts

    def test_datetime_override_encode(self):
        assert iso_schema.dump(self.dc_iso) == self.dc_iso_json

    def test_datetime_override_decode(self):
        assert iso_schema.load(self.dc_iso_json) == self.dc_iso
