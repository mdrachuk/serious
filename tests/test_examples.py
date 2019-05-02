from dataclasses import dataclass
from typing import Set

from serious.json import json_schema, Loading


@dataclass(frozen=True)
class Student:
    id: int = 0
    name: str = "student"


@dataclass(frozen=True)
class Professor:
    id: int
    name: str


@dataclass(frozen=True)
class Course:
    id: int
    name: str
    professor: Professor
    students: Set[Student]


s1 = Student(1, 'student')
s2 = Student(2, 'student')
p = Professor(1, 'professor')
c = Course(1, 'course', p, {s1})


class TestEncoder:
    def test_student(self):
        assert json_schema(Student).dump(s1) == '{"id": 1, "name": "student"}'

    def test_professor(self):
        assert json_schema(Professor).dump(p) == '{"id": 1, "name": "professor"}'

    def test_course(self):
        assert json_schema(Course).dump(c) == '{"id": 1, ' \
                                         '"name": "course", ' \
                                         '"professor": {"id": 1, "name": "professor"}, ' \
                                         '"students": [{"id": 1, "name": "student"}]}'

    def test_students_missing(self):
        s1_anon = Student(1, 'student')
        s2_anon = Student(2, 'student')
        one = [s1_anon, s2_anon]
        two = [s2_anon, s1_anon]
        actual = json_schema(Student, load=Loading(allow_missing=True)).load_all('[{"id": 1}, {"id": 2}]')
        assert actual == one or actual == two
