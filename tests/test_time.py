import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone

import m2


@dataclass
class DataClassWithDatetime:
    created_at: datetime


@dataclass
class DataClassWithIsoDatetime:
    created_at: datetime = field(
        metadata={'m2': {
            'encoder': datetime.isoformat,
            'decoder': datetime.fromisoformat,
        }})


class TestTime:
    dt = datetime(2018, 11, 17, 16, 55, 28, 456753, tzinfo=timezone.utc)
    tz = timezone.utc

    ts = dt.timestamp()
    dc_ts_json = f'{{"created_at": {ts}}}'
    dc_ts = DataClassWithDatetime(datetime.fromtimestamp(ts, tz=tz))

    if sys.version_info >= (3, 7):
        iso = dt.isoformat()
        dc_iso_json = f'{{"created_at": "{iso}"}}'
        dc_iso = DataClassWithIsoDatetime(datetime.fromisoformat(iso))

    def test_datetime_encode(self):
        assert m2.asjson(self.dc_ts) == self.dc_ts_json

    def test_datetime_decode(self):
        assert m2.load(DataClassWithDatetime).from_(self.dc_ts_json) == self.dc_ts

    def test_datetime_override_encode(self):
        assert m2.asjson(self.dc_iso) == self.dc_iso_json

    def test_datetime_override_decode(self):
        assert m2.load(DataClassWithIsoDatetime).from_(self.dc_iso_json) == self.dc_iso
