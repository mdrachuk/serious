import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone

import pytest
from marshmallow import fields

import m2
from m2 import load


@dataclass
class DataClassWithDatetime:
    created_at: datetime


if sys.version_info >= (3, 7):
    @dataclass
    class DataClassWithIsoDatetime:
        created_at: datetime = field(
            metadata={'m2': {
                'encoder': datetime.isoformat,
                'decoder': datetime.fromisoformat,
                'mm_field': fields.DateTime(format='iso')
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
        assert load(DataClassWithDatetime).one(self.dc_ts_json) == self.dc_ts

    @pytest.mark.skipif(sys.version_info < (3, 7), reason="requires python3.7")
    def test_datetime_override_encode(self):
        assert m2.asjson(self.dc_iso) == self.dc_iso_json

    @pytest.mark.skipif(sys.version_info < (3, 7), reason="requires python3.7")
    def test_datetime_override_decode(self):
        assert load(DataClassWithIsoDatetime).one(self.dc_iso_json) == self.dc_iso
