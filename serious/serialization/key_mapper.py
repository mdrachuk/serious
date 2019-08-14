from abc import ABC, abstractmethod


class KeyMapper(ABC):

    @abstractmethod
    def to_model(self, item: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def to_serialized(self, item: str) -> str:
        raise NotImplementedError


class NoopKeyMapper(KeyMapper):

    def to_model(self, item: str) -> str:
        return item

    def to_serialized(self, item: str) -> str:
        return item
