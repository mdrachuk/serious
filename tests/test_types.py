from datetime import datetime, timezone
from typing import Any

import pytest

from serious import Timestamp, validate, ValidationError
from serious.types import Email


class TestTimestamp:

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


vader = 'vader@death-star.gov'
luke = 'luke+jediacademy@skywalkers.org'


class TestEmail:

    def test_init(self):
        assert Email(vader) == vader

    def test_case_insensitive(self):
        assert Email('example@example.org') == Email('eXaMPLe@exAmPLE.ORg')

    def test_properties(self):
        vader_address = Email(vader)
        assert vader_address.username == 'vader'
        assert vader_address.domain == 'death-star.gov'
        assert vader_address.label is None

        luke_address = Email(luke)
        assert luke_address.username == 'luke'
        assert luke_address.domain == 'skywalkers.org'
        assert luke_address.label == 'jediacademy'

    def test_repr(self):
        assert repr(Email(vader)) == '<Email vader@death-star.gov>'

    def test_str(self):
        assert str(Email(vader)) == 'vader@death-star.gov'

    def test_immutability(self):
        address = Email(luke)
        with pytest.raises(AttributeError):
            address.username = 'leia'
        with pytest.raises(AttributeError):
            address.domain = 'nabu.gov'
        with pytest.raises(AttributeError):
            address.label = 'resistance'

    def test_validation(self):
        assert validate(Email(vader)) is None
        assert validate(Email(luke)) is None
        assert validate(Email('admin@example.international')) is None
        assert validate(Email('голова@2024.укр')) is None
        assert validate(Email('голова+пора@2024.укр')) is None
        with pytest.raises(ValidationError):
            validate(Email('голова++пора@2024.укр'))
        with pytest.raises(ValidationError):
            validate(Email('admin+example+example@example.org'))
        with pytest.raises(ValidationError):
            validate(Email('+admin@example.org'))
