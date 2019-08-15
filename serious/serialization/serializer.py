from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, TYPE_CHECKING

from serious.descriptors import TypeDescriptor

M = TypeVar('M')  # Python model value
S = TypeVar('S')  # Serialized value

if TYPE_CHECKING:
    from .model import SeriousModel
    from .context import Loading, Dumping


class Serializer(Generic[M, S], ABC):

    @abstractmethod
    def load(self, value: S, ctx: Loading) -> M:
        raise NotImplementedError

    @abstractmethod
    def dump(self, value: M, ctx: Dumping) -> S:
        raise NotImplementedError


class FieldSerializer(Serializer[S, M], ABC):
    """
    A abstract field serializer defining a constructor invoked by serious `dump`, `load` and class `fits` methods.

    Field serializers are provided to a serious model (`JsonModel`_, `DictModel`_, `YamlModel`_) serializers
    parameter in an order in which they will be tested for fitness in.

    A clean way to add custom serializers to the defaults is to use the `field_serializers` function.

    .. _JsonModel: serious.json.model.JsonModel
    .. _DictModel: serious.dict.model.DictModel
    .. _YamlModel: serious.yaml.model.YamlModel
    """

    def __init__(self, descriptor: TypeDescriptor, root_model: 'SeriousModel'):
        self.type = descriptor
        self.root = root_model

    @classmethod
    @abstractmethod
    def fits(cls, desc: TypeDescriptor) -> bool:
        """
        A predicate returning `True` if this serializer fits to load/dump data for the provided field.

        The first fitting `FieldSerializer` from the list provided to the model will be used.

        Beware, the `field.type.cls` property can be an instance of a generic alias which will error,
        if using `issubclass` which expects a `type`.
        """
        raise NotImplementedError
