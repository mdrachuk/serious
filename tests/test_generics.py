from dataclasses import dataclass
from typing import TypeVar, Generic, List
from uuid import UUID

from serious import DictModel

ID = TypeVar('ID')
M = TypeVar('M')
C = TypeVar('C')

NUMBER = TypeVar('NUMBER', int, float)

@dataclass(frozen=True)
class Envelope(Generic[ID, M]):
    id: ID
    message: M


@dataclass(frozen=True)
class Message(Generic[C]):
    content: C


class TestSimpleGeneric:
    def setup_class(self):
        self.model = DictModel(Envelope[int, str])
        self.o = Envelope(1, 'test')
        self.d = {'id': 1, 'message': 'test'}

    def test_load(self):
        actual = self.model.load(self.d)
        assert actual == self.o

    def test_dump(self):
        actual = self.model.dump(self.o)
        assert actual == self.d


class TestNestedGeneric:

    def setup_class(self):
        self.model = DictModel(Envelope[int, Message[str]])
        self.o = Envelope(2, Message('test'))
        self.d = {'id': 2, 'message': {'content': 'test'}}

    def test_load(self):
        actual = self.model.load(self.d)
        assert actual == self.o

    def test_dump(self):
        actual = self.model.dump(self.o)
        assert actual == self.d


@dataclass(frozen=True)
class EnvelopeEnvelope(Envelope[UUID, Message[Envelope[int, Message[str]]]]):
    pass


class TestComplexGeneric:

    def setup_class(self):
        self.model = DictModel(EnvelopeEnvelope)
        uuid_str = 'd1d61dd7-c036-47d3-a6ed-91cc2e885fc8'
        self.o = EnvelopeEnvelope(UUID(uuid_str), Message(Envelope(3, Message('hello'))))
        self.d = {
            'id': uuid_str,
            'message': {'content': {'id': 3, 'message': {'content': 'hello'}}}
        }

    def test_load(self):
        actual = self.model.load(self.d)
        assert actual == self.o

    def test_dump(self):
        actual = self.model.dump(self.o)
        assert actual == self.d


@dataclass(frozen=True)
class Author:
    name: str


@dataclass(frozen=True)
class Recipe:
    authors: List[Author]
    tags: List[str]


class TestCollectionGeneric:

    def setup_class(self):
        self.model = DictModel(Recipe)
        self.o = Recipe([Author('harry'), Author('hermione')], ['magic', 'shrooms'])
        self.d = {'authors': [{'name': 'harry'}, {'name': 'hermione'}], 'tags': ['magic', 'shrooms']}

    def test_load(self):
        actual = self.model.load(self.d)
        assert actual == self.o

    def test_dump(self):
        actual = self.model.dump(self.o)
        assert actual == self.d


@dataclass
class NumberContainer(Generic[NUMBER]):
    number: NUMBER


class TestConstrainedGeneric:

    def setup_class(self):
        self.model = DictModel(NumberContainer)
        self.o = NumberContainer(42)
        self.d = {'number': {"__type__": "int", "__value__": 42}}

    def test_load(self):
        actual = self.model.load(self.d)
        assert actual == self.o

    def test_dump(self):
        actual = self.model.dump(self.o)
        assert actual == self.d


class TestConstrainedGenericParametrized:

    def setup_class(self):
        self.model = DictModel(NumberContainer[float])
        self.o = NumberContainer(42.0)
        self.d = {'number': 42.0}

    def test_load(self):
        actual = self.model.load(self.d)
        assert actual == self.o

    def test_dump(self):
        actual = self.model.dump(self.o)
        assert actual == self.d
