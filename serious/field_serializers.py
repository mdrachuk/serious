import abc
import copy
from typing import Callable, Any

from serious.attr import Attr
from serious.context import SerializationContext
from serious.utils import Primitive

if False:  # For referencing typings
    from serious.serialization import SeriousSerializer

DumpF = Callable[[Any], Primitive]
LoadF = Callable[[Primitive], Any]


class FieldSerializer(abc.ABC):
    def __init__(self, attr: Attr):
        self._attr = attr

    def with_stack(self):
        entry = f'.{self.attr.name}'
        serializer = copy.copy(self)
        setattr(serializer, 'load', with_stack(self.load, entry))
        setattr(serializer, 'dump', with_stack(self.dump, entry))
        return serializer

    @property
    def attr(self):
        return self._attr

    @abc.abstractmethod
    def dump(self, value: Any, ctx: SerializationContext) -> Primitive:
        pass

    @abc.abstractmethod
    def load(self, value: Primitive, ctx: SerializationContext) -> Any:
        pass


def with_stack(f: Callable, entry: str = None, entry_factory: Callable = None):
    if (not entry and not entry_factory) or (entry and entry_factory):
        raise Exception('Only one of entry and entry_factory is expected')

    def _wrap(*args):
        ctx: SerializationContext = args[-1]
        with ctx.enter(entry or entry_factory()):
            return f(*args)

    return _wrap


class DirectFieldSerializer(FieldSerializer):
    def __init__(self, attr: Attr, load: LoadF, dump: DumpF):
        super().__init__(attr)
        self._load = load
        self._dump = dump

    def load(self, value: Primitive, ctx: SerializationContext) -> Any:
        return self._load(value)

    def dump(self, value: Any, ctx: SerializationContext) -> Primitive:
        return self._dump(value)


class MetadataFieldSerializer(DirectFieldSerializer):
    def __init__(self, attr: Attr):
        super().__init__(attr, load=attr.serious_metadata['load'], dump=attr.serious_metadata['dump'])


class CollectionFieldSerializer(FieldSerializer):
    def __init__(self, attr: Attr, each: FieldSerializer):
        super().__init__(attr)
        self._load_item = each.load
        self._dump_item = each.dump

    def with_stack(self):
        serializer = super().with_stack()

        item_entry = lambda i, *_: f'[{i}]'
        setattr(serializer, 'load_item', with_stack(self.load_item, entry_factory=item_entry))
        setattr(serializer, 'dump_item', with_stack(self.dump_item, entry_factory=item_entry))

        return serializer

    def load(self, value: Primitive, ctx: SerializationContext) -> Any:
        items = [self.load_item(i, item, ctx) for i, item in enumerate(value)]  # type: ignore # value is a collection
        return self._attr.type.__origin__(items)

    def dump(self, value: Any, ctx: SerializationContext) -> Primitive:
        return [self.dump_item(i, item, ctx) for i, item in enumerate(value)]

    def load_item(self, i: int, value: Primitive, ctx: SerializationContext):
        return self._load_item(value, ctx)

    def dump_item(self, i: int, value: Any, ctx: SerializationContext):
        return self._dump_item(value, ctx)


class DataclassFieldSerializer(FieldSerializer):
    def __init__(self, attr: Attr, serializer: 'SeriousSerializer'):
        super().__init__(attr)
        self._serializer = serializer

    def load(self, value: Primitive, ctx: SerializationContext) -> Any:
        return self._serializer.load(value, ctx)  # type: ignore # type: ignore # value always a mapping

    def dump(self, value: Any, ctx: SerializationContext) -> Primitive:
        return self._serializer.dump(value, ctx)


class DictFieldSerializer(FieldSerializer):
    def __init__(self, attr: Attr, key: FieldSerializer, value: FieldSerializer):
        super().__init__(attr)
        self._dump_key = key.dump
        self._load_key = key.load
        self._dump_value = value.dump
        self._load_value = value.load

    def with_stack(self):
        serializer = super().with_stack()

        value_entry = lambda key, *_: f'[{key}]'
        setattr(serializer, 'dump_value', with_stack(self.dump_value, entry_factory=value_entry))
        setattr(serializer, 'load_value', with_stack(self.load_value, entry_factory=value_entry))

        key_entry = lambda key, *_: f'${key}'
        setattr(serializer, 'dump_key', with_stack(self.dump_key, entry_factory=key_entry))
        setattr(serializer, 'load_key', with_stack(self.load_key, entry_factory=key_entry))

        return serializer

    def load(self, data: Primitive, ctx: SerializationContext) -> Any:
        items = {
            self.load_key(key, ctx): self.load_value(key, value, ctx)
            for key, value in data.items()  # type: ignore # data is always a dict
        }
        return self.attr.type.__origin__(items)

    def dump(self, d: Any, ctx: SerializationContext) -> Primitive:
        return {self.dump_key(key, ctx): self.dump_value(key, value, ctx) for key, value in d.items()}

    def load_value(self, key: str, value: Primitive, ctx: SerializationContext) -> Any:
        return self._load_value(value, ctx)

    def dump_value(self, key: str, value: Any, ctx: SerializationContext) -> Primitive:
        return self._dump_value(value, ctx)

    def load_key(self, key: str, ctx: SerializationContext) -> Any:
        return self._load_key(key, ctx)

    def dump_key(self, key: Any, ctx: SerializationContext) -> str:
        return str(self._dump_key(key, ctx))


class OptionalFieldSerializer(FieldSerializer):
    def __init__(self, attr: Attr, serializer: FieldSerializer):
        super().__init__(attr)
        self._serializer = serializer

    def dump(self, value: Any, ctx: SerializationContext) -> Primitive:
        return None if value is None else self._serializer.dump(value, ctx)

    def load(self, value: Primitive, ctx: SerializationContext) -> Any:
        return None if value is None else self._serializer.load(value, ctx)
