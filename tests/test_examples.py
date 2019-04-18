from dataclasses import dataclass
from typing import Set

import serious


@dataclass(frozen=True)
class Student:
    id: int = 0
    name: str = ""


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
        assert serious.asjson(s1) == '{"id": 1, "name": "student"}'

    def test_professor(self):
        assert serious.asjson(p) == '{"id": 1, "name": "professor"}'

    def test_course(self):
        assert serious.asjson(c) == '{"id": 1, ' \
                               '"name": "course", ' \
                               '"professor": {"id": 1, "name": "professor"}, ' \
                               '"students": [{"id": 1, "name": "student"}]}'

    def test_students_missing(self):
        s1_anon = Student(1, '')
        s2_anon = Student(2, '')
        one = [s1_anon, s2_anon]
        two = [s2_anon, s1_anon]
        actual = serious.load_all(Student).from_('[{"id": 1}, {"id": 2}]')
        assert actual == one or actual == two
