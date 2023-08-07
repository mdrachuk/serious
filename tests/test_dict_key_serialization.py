from dataclasses import dataclass
from datetime import date
from typing import Dict

from serious import DictModel


@dataclass
class DailyRates:
    daily_rates: Dict[date, int]


class TestTypedDict:
    def setup(self):
        self.model = DictModel(DailyRates)

    def test_load(self):
        o = self.model.load(
            {
                'daily_rates': {
                    '2022-01-01': 100,
                    '2022-01-02': 80,
                    '2022-01-03': 87,
                }
            }
        )

        assert o == DailyRates({
            date(2022, 1, 1): 100,
            date(2022, 1, 2): 80,
            date(2022, 1, 3): 87,
        })

    def test_dump(self):
        d = self.model.dump(DailyRates(
            {
                date(2022, 1, 1): -5,
                date(2022, 1, 2): 0,
                date(2022, 1, 3): 5,
            }
        ))

        assert d == {
            'daily_rates': {
                '2022-01-01': -5,
                '2022-01-02': 0,
                '2022-01-03': 5,
            }
        }
