from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from serious.descriptors import Descriptor

OBJECT_TYPE = TypeVar("OBJECT_TYPE")  # Python model value
PRIMITIVE_TYPE = TypeVar("PRIMITIVE_TYPE")  # Serialized value


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

    def __init__(self, descriptor, root_model):
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
    def load(self, primitive, _):
        ...

    @abstractmethod
    def dump(self, o, _):
        ...

    def load_nested(self, step, primitive, ctx):
        ctx.enter(step, primitive)
        result = self.load(primitive, ctx)
        if ctx.validating:
            ctx.validate(result)
        ctx.exit()
        return result

    def dump_nested(self, step, o, ctx):
        ctx.enter(step, o)
        if ctx.validating:
            ctx.validate(o)
        result = self.dump(o, ctx)
        ctx.exit()
        return result
