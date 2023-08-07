from dataclasses import dataclass
from datetime import date
from typing import TypedDict, List

from serious import DictModel


class MillionaireAnswers(TypedDict):
    a: str
    b: str
    c: str
    d: str


@dataclass
class MillionaireQuestion:
    question: str
    answers: MillionaireAnswers


class TestTypedDict:
    def setup(self):
        self.model = DictModel(MillionaireQuestion)

    def test_load(self):
        o = self.model.load(
            {
                "question": "What type of hepatitis does not exist?",
                "answers": {"a": "A", "b": "B", "c": "C", "d": "F"}
            }
        )
        assert type(o.answers) is dict
        assert o.answers['a'] == 'A'
        assert o.answers['b'] == 'B'
        assert o.answers['c'] == 'C'
        assert o.answers['d'] == 'F'

    def test_dump(self):
        d = self.model.dump(
            MillionaireQuestion(
                'Which of the following is the largest?',
                {
                    'a': 'A Peanut',
                    'b': 'An Elephant',
                    'c': 'The Moon',
                    'd': 'A Kettle',
                }
            )
        )

        assert d == {
            'question': 'Which of the following is the largest?',
            'answers': {
                'a': 'A Peanut',
                'b': 'An Elephant',
                'c': 'The Moon',
                'd': 'A Kettle',
            }
        }


@dataclass
class Contact:
    first_name: str
    last_name: str


class CalendarDay(TypedDict):
    day: date
    birthdays: List[Contact]


@dataclass
class Calendar:
    days: List[CalendarDay]


class TestComplexTypedDicts:
    def setup(self):
        self.model = DictModel(Calendar)

    def test_load(self):
        o = self.model.load({
            "days": [
                {"day": "1996-03-03", "birthdays": [{"first_name": "Mykhailo", "last_name": "Drachuk"}]}
            ]
        })
        assert o == Calendar([{"day": date(1996, 3, 3), "birthdays": [Contact('Mykhailo', 'Drachuk')]}])

    def test_dump(self):
        d = self.model.dump(Calendar([{"day": date(1996, 3, 3), "birthdays": [Contact('Mykhailo', 'Drachuk')]}]))
        assert d == {"days": [{"day": "1996-03-03", "birthdays": [{"first_name": "Mykhailo", "last_name": "Drachuk"}]}]}
