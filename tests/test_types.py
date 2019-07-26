from datetime import datetime, timezone
from typing import Any

import pytest

from serious import Timestamp


class TestTimestamp:

    def test_alias(self):
        assert Timestamp is Timestamp

    def test_int_init(self):
        assert Timestamp(123).value == 123

    def test_float_init(self):
        assert Timestamp(123.123).value == 123.123

    def test_iso_init(self):
        assert Timestamp('2018-11-17T16:55:28.456753+00:00').value == 1542473728.456753

    def test_datetime_init(self):
        dt = datetime(2018, 11, 17, 16, 55, 28, 456753, tzinfo=timezone.utc)
        assert Timestamp(dt).value == 1542473728.456753

    def test_as_datetime(self):
        dt = datetime(2018, 11, 17, 16, 55, 28, 456753, tzinfo=timezone.utc)
        assert Timestamp(1542473728.456753).as_datetime() == dt

    def test_repr(self):
        assert repr(Timestamp(1)) == '<Timestamp 1970-01-01T00:00:01+00:00 (1.0)>'

    def test_str(self):
        assert str(Timestamp(1)) == '1970-01-01T00:00:01+00:00'

    def test_comparison(self):
        t1 = Timestamp(1)
        t1_copy = Timestamp('1970-01-01T00:00:01+00:00')
        t2 = Timestamp(1.000001)
        t2_copy = Timestamp('1970-01-01T00:00:01.000001+00:00')
        assert t1 == t1_copy
        assert t2 == t2_copy
        assert t2 != t1

        assert t1 <= t1_copy
        assert t1 <= t2
        assert t1 < t2

        assert t2 >= t2_copy
        assert t2 >= t1
        assert t2 > t1

    def test_fail_comparison(self):
        t: Any = Timestamp(1)
        with pytest.raises(NotImplementedError):
            assert t == 999
        with pytest.raises(NotImplementedError):
            assert t != 999
        with pytest.raises(NotImplementedError):
            assert t <= 999
        with pytest.raises(NotImplementedError):
            assert t <= 999
        with pytest.raises(NotImplementedError):
            assert t < 999
        with pytest.raises(NotImplementedError):
            assert t >= 999
        with pytest.raises(NotImplementedError):
            assert t >= 999
        with pytest.raises(NotImplementedError):
            assert t > 999

    def test_immutability(self):
        t = Timestamp(1)
        with pytest.raises(AttributeError):
            t.value = 2
        with pytest.raises(AttributeError):
            t.something = 3
