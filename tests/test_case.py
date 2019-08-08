from dataclasses import dataclass

from serious import JsonModel


@dataclass
class Snack:
    butterbeer: int
    dragon_tartare: int
    hogwarts_steak_and_kidney_pie_: int
    _pumpkin__fizz: int


def test_json_transforms_case_by_default():
    model = JsonModel(Snack)
    actual = model.dump(Snack(1, 2, 3, 4))
    expected = '{"butterbeer": 1, "dragonTartare": 2, "hogwartsSteakAndKidneyPie": 3, "pumpkinFizz": 4}'
    assert actual == expected


def test_json_transforms_case():
    model = JsonModel(Snack, camel_case=True)
    actual = model.dump(Snack(1, 2, 3, 4))
    expected = '{"butterbeer": 1, "dragonTartare": 2, "hogwartsSteakAndKidneyPie": 3, "pumpkinFizz": 4}'
    assert actual == expected


def test_json_skips_transformation():
    model = JsonModel(Snack, camel_case=False)
    actual = model.dump(Snack(1, 2, 3, 4))
    expected = '{"butterbeer": 1, "dragon_tartare": 2, "hogwarts_steak_and_kidney_pie_": 3, "_pumpkin__fizz": 4}'
    assert actual == expected
