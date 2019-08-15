"""Map dataclass field names to different keys when serializing.

The biggest case to remap keys is switch between dataclass snake_case and JSON camelCase traditions.
We honor foreign traditions, so the JSON model does by default.

Remapping is implementing by creating a custom KeyMapper and passing it as a parameter to `SeriousModel`.
"""

__all__ = ['KeyMapper', 'NoopKeyMapper']

from abc import ABC, abstractmethod


class KeyMapper(ABC):
    """A two way mapping of field names to serialized data keys.

    Implement this abstract base class and pass it to `SeriousModel`.
    """

    @abstractmethod
    def to_model(self, key: str) -> str:
        """
        :param key: the key of a serialized object
        :return: a field name of a model
        """
        raise NotImplementedError

    @abstractmethod
    def to_serialized(self, field: str) -> str:
        """
        :param field: the field name of a model
        :return: a key of a serialized object
        """
        raise NotImplementedError


class NoopKeyMapper(KeyMapper):
    """A key mapper that does nothing."""

    def to_model(self, key: str) -> str:
        return key

    def to_serialized(self, field: str) -> str:
        return field
