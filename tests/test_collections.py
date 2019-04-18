from collections import deque

from serious import load, asjson
from tests.entities import (DataClassIntImmutableDefault,
                            DataClassMutableDefaultDict,
                            DataClassMutableDefaultList, DataClassWithDeque,
                            DataClassWithDict, DataClassWithDictInt,
                            DataClassWithFrozenSet, DataClassWithList,
                            DataClassWithListStr, DataClassWithMyCollection,
                            DataClassWithOptional, DataClassWithOptionalStr,
                            DataClassWithSet, DataClassWithTuple,
                            DataClassWithUnionIntNone, MyCollection)


class TestEncoder:
    def test_list(self):
        assert asjson(DataClassWithList([1])) == '{"xs": [1]}'

    def test_list_str(self):
        assert asjson(DataClassWithListStr(['1'])) == '{"xs": ["1"]}'

    def test_dict(self):
        assert asjson(DataClassWithDict({'1': 'a'})) == '{"kvs": {"1": "a"}}'

    def test_dict_int(self):
        assert asjson(DataClassWithDictInt({1: 'a'})) == '{"kvs": {"1": "a"}}'

    def test_set(self):
        assert asjson(DataClassWithSet({1})) == '{"xs": [1]}'

    def test_tuple(self):
        assert asjson(DataClassWithTuple((1,))) == '{"xs": [1]}'

    def test_frozenset(self):
        assert asjson(DataClassWithFrozenSet(frozenset([1]))) == '{"xs": [1]}'

    def test_deque(self):
        assert asjson(DataClassWithDeque(deque([1]))) == '{"xs": [1]}'

    def test_optional(self):
        assert asjson(DataClassWithOptional(1)) == '{"x": 1}'
        assert asjson(DataClassWithOptional(None)) == '{"x": null}'

    def test_optional_str(self):
        assert asjson(DataClassWithOptionalStr('1')) == '{"x": "1"}'
        assert asjson(DataClassWithOptionalStr(None)) == '{"x": null}'
        assert asjson(DataClassWithOptionalStr()) == '{"x": null}'

    def test_union_int_none(self):
        assert asjson(DataClassWithUnionIntNone(1)) == '{"x": 1}'
        assert asjson(DataClassWithUnionIntNone(None)) == '{"x": null}'

    def test_my_collection(self):
        assert asjson(DataClassWithMyCollection(MyCollection([1]))) == '{"xs": [1]}'

    def test_immutable_default(self):
        assert asjson(DataClassIntImmutableDefault()) == '{"x": 0}'

    def test_mutable_default_list(self):
        assert asjson(DataClassMutableDefaultList()) == '{"xs": []}'

    def test_mutable_default_dict(self):
        assert asjson(DataClassMutableDefaultDict()) == '{"xs": {}}'


class TestDecoder:
    def test_list(self):
        actual = load(DataClassWithList).from_('{"xs": [1]}')
        expected = DataClassWithList([1])
        assert (actual == expected)

    def test_list_str(self):
        actual = load(DataClassWithListStr).from_('{"xs": ["1"]}')
        expected = DataClassWithListStr(["1"])
        assert actual == expected

    def test_dict(self):
        actual = load(DataClassWithDict).from_('{"kvs": {"1": "a"}}')
        expected = DataClassWithDict({'1': 'a'})
        assert actual == expected

    def test_dict_int(self):
        actual = load(DataClassWithDictInt).from_('{"kvs": {"1": "a"}}')
        expected = DataClassWithDictInt({1: 'a'})
        assert actual == expected

    def test_set(self):
        actual = load(DataClassWithSet).from_('{"xs": [1]}')
        expected = DataClassWithSet({1})
        assert actual == expected

    def test_tuple(self):
        actual = load(DataClassWithTuple).from_('{"xs": [1]}')
        expected = DataClassWithTuple((1,))
        assert actual == expected

    def test_frozenset(self):
        actual = load(DataClassWithFrozenSet).from_('{"xs": [1]}')
        expected = DataClassWithFrozenSet(frozenset([1]))
        assert actual == expected

    def test_deque(self):
        actual = load(DataClassWithDeque).from_('{"xs": [1]}')
        expected = DataClassWithDeque(deque([1]))
        assert (actual == expected)

    def test_optional(self):
        actual1 = load(DataClassWithOptional).from_('{"x": 1}')
        expected1 = DataClassWithOptional(1)
        assert actual1 == expected1

        actual2 = load(DataClassWithOptional).from_('{"x": null}')
        expected2 = DataClassWithOptional(None)
        assert actual2 == expected2

    def test_optional_str(self):
        actual1 = load(DataClassWithOptionalStr).from_('{"x": "1"}')
        expected1 = DataClassWithOptionalStr("1")
        assert actual1 == expected1

        actual2 = load(DataClassWithOptionalStr).from_('{"x": null}')
        expected2 = DataClassWithOptionalStr(None)
        assert actual2 == expected2

        actual3 = load(DataClassWithOptionalStr, infer_missing=True).from_('{}')
        expected3 = DataClassWithOptionalStr()
        assert actual3 == expected3

    def test_my_collection(self):
        actual = load(DataClassWithMyCollection).from_('{"xs": [1]}')
        expected = DataClassWithMyCollection(MyCollection([1]))
        assert actual == expected

    def test_immutable_default(self):
        actual1 = load(DataClassIntImmutableDefault).from_('{"x": 0}')
        expected1 = DataClassIntImmutableDefault()
        assert actual1 == expected1

    def test_mutable_default_list(self):
        expected = DataClassMutableDefaultList()

        actual1 = load(DataClassMutableDefaultList).from_('{"xs": []}')
        assert actual1 == expected

        actual2 = load(DataClassMutableDefaultList, infer_missing=True).from_('{}')
        assert actual2 == expected

    def test_mutable_default_dict(self):
        expected = DataClassMutableDefaultDict()

        actual1 = load(DataClassMutableDefaultDict).from_('{"kvs": {}}')
        assert actual1 == expected

        actual2 = load(DataClassMutableDefaultDict, infer_missing=True).from_('{}')
        assert actual2 == expected
