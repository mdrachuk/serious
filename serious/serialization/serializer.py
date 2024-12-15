from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, TYPE_CHECKING

from serious.descriptors import Descriptor

OBJECT_TYPE = TypeVar('OBJECT_TYPE')  # Python model value
PRIMITIVE_TYPE = TypeVar('PRIMITIVE_TYPE')  # Serialized value



if TYPE_CHECKING:
    from .model import SeriousModel
    from .context import Loading, Dumping


class Serializer(Generic[OBJECT_TYPE, PRIMITIVE_TYPE], ABC):
    """
    A abstract field serializer defining a constructor invoked by serious `dump`, `load` and class `fits` methods.

    Field serializers are provided to a serious model (`JsonModel`_, `DictModel`_, `YamlModel`_) serializers
    parameter in an order in which they will be tested for fitness in.

    A clean way to add custom serializers to the defaults is to use the `field_serializers` function.

    .. _JsonModel: serious.json.model.JsonModel
    .. _DictModel: serious.dict.model.DictModel
    .. _YamlModel: serious.yaml.model.YamlModel
    """

    def __init__(self, descriptor: Descriptor, root_model: 'SeriousModel'):
        self.type = descriptor
        self.root = root_model

    @classmethod
    @abstractmethod
    def fits(cls, desc: Descriptor) -> bool:
        """
        A predicate returning `True` if this serializer fits to load/dump data for the provided field.

        The first fitting `Serializer` from the list provided to the model will be used.

        Beware, the `field.type.cls` property can be an instance of a generic alias which will error,
        if using `issubclass` which expects a `type`.
        """
        raise NotImplementedError

    @abstractmethod
    def load(self, value: PRIMITIVE_TYPE, ctx: Loading) -> OBJECT_TYPE:
        raise NotImplementedError

    @abstractmethod
    def dump(self, value: OBJECT_TYPE, ctx: Dumping) -> PRIMITIVE_TYPE:
        raise NotImplementedError
