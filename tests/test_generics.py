from dataclasses import dataclass
from typing import TypeVar, Generic, List
from uuid import UUID

from serious.dict import DictSerializer

ID = TypeVar('ID')
M = TypeVar('M')
C = TypeVar('C')


@dataclass(frozen=True)
class Envelope(Generic[ID, M]):
    id: ID
    message: M


@dataclass(frozen=True)
class Message(Generic[C]):
    content: C


class TestSimpleGeneric:
    def setup_class(self):
        self.schema = DictSerializer(Envelope[int, str])
        self.o = Envelope(1, 'test')
        self.d = {'id': 1, 'message': 'test'}

    def test_load(self):
        actual = self.schema.load(self.d)
        assert actual == self.o

    def test_dump(self):
        actual = self.schema.dump(self.o)
        assert actual == self.d


class TestNestedGeneric:

    def setup_class(self):
        self.schema = DictSerializer(Envelope[int, Message[str]])
        self.o = Envelope(2, Message('test'))
        self.d = {'id': 2, 'message': {'content': 'test'}}

    def test_load(self):
        actual = self.schema.load(self.d)
        assert actual == self.o

    def test_dump(self):
        actual = self.schema.dump(self.o)
        assert actual == self.d


@dataclass(frozen=True)
class EnvelopeEnvelope(Envelope[UUID, Message[Envelope[int, Message[str]]]]):
    pass


class TestComplexGeneric:

    def setup_class(self):
        self.schema = DictSerializer(EnvelopeEnvelope)
        uuid_str = 'd1d61dd7-c036-47d3-a6ed-91cc2e885fc8'
        self.o = EnvelopeEnvelope(UUID(uuid_str), Message(Envelope(3, Message('hello'))))
        self.d = {
            'id': uuid_str,
            'message': {'content': {'id': 3, 'message': {'content': 'hello'}}}
        }

    def test_load(self):
        actual = self.schema.load(self.d)
        assert actual == self.o

    def test_dump(self):
        actual = self.schema.dump(self.o)
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
        self.schema = DictSerializer(Recipe)
        self.o = Recipe([Author('harry'), Author('hermione')], ['magic', 'shrooms'])
        self.d = {'authors': [{'name': 'harry'}, {'name': 'hermione'}], 'tags': ['magic', 'shrooms']}

    def test_load(self):
        actual = self.schema.load(self.d)
        assert actual == self.o

    def test_dump(self):
        actual = self.schema.dump(self.o)
        assert actual == self.d
