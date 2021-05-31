from serious import JsonModel, FrozenList
from tests.entities import (DataclassIntImmutableDefault,
                            DataclassMutableDefaultDict, DataclassMutableDefaultList,
                            DataclassWithDict, DataclassWithFrozenSet, DataclassWithList,
                            DataclassWithListStr, DataclassWithOptional, DataclassWithOptionalStr,
                            DataclassWithSet, DataclassWithTuple, DataclassWithUnionIntNone, DataclassWithFrozenList,
                            DataclassWithTupleCollection)


class TestEncoder:
    def test_list(self):
        assert JsonModel(DataclassWithList).dump(DataclassWithList([1])) == '{"xs": [1]}'

    def test_list_str(self):
        assert JsonModel(DataclassWithListStr).dump(DataclassWithListStr(['1', '2'])) == '{"xs": ["1", "2"]}'

    def test_dict(self):
        assert JsonModel(DataclassWithDict).dump(DataclassWithDict({'1': 'a'})) == '{"kvs": {"1": "a"}}'

    def test_set(self):
        assert JsonModel(DataclassWithSet).dump(DataclassWithSet({1, 2})) == '{"xs": [1, 2]}'

    def test_tuple(self):
        assert JsonModel(DataclassWithTuple).dump(DataclassWithTuple((1, "2"))) == '{"xs": [1, "2"]}'

    def test_tuple_collection(self):
        assert JsonModel(DataclassWithTupleCollection).dump(DataclassWithTupleCollection((1, 2))) == '{"xs": [1, 2]}'

    def test_frozenlist(self):
        model = JsonModel(DataclassWithFrozenList)
        assert model.dump(DataclassWithFrozenList(FrozenList([1, 2, 3]))) == '{"xs": [1, 2, 3]}'
        assert model.dump(DataclassWithFrozenList((1, 2, 3))) == '{"xs": [1, 2, 3]}'

    def test_frozenset(self):
        assert JsonModel(DataclassWithFrozenSet).dump(DataclassWithFrozenSet(frozenset([1]))) == '{"xs": [1]}'

    def test_optional(self):
        s = JsonModel(DataclassWithOptional)
        assert s.dump(DataclassWithOptional(1)) == '{"x": 1}'
        assert s.dump(DataclassWithOptional(None)) == '{"x": null}'

    def test_optional_str(self):
        s = JsonModel(DataclassWithOptionalStr)
        assert s.dump(DataclassWithOptionalStr('1')) == '{"x": "1"}'
        assert s.dump(DataclassWithOptionalStr(None)) == '{"x": null}'
        assert s.dump(DataclassWithOptionalStr()) == '{"x": null}'

    def test_union_int_none(self):
        s = JsonModel(DataclassWithUnionIntNone)
        assert s.dump(DataclassWithUnionIntNone(1)) == '{"x": 1}'
        assert s.dump(DataclassWithUnionIntNone(None)) == '{"x": null}'

    def test_immutable_default(self):
        assert JsonModel(DataclassIntImmutableDefault).dump(DataclassIntImmutableDefault()) == '{"x": 0}'

    def test_mutable_default_list(self):
        assert JsonModel(DataclassMutableDefaultList).dump(DataclassMutableDefaultList()) == '{"xs": []}'

    def test_mutable_default_dict(self):
        assert JsonModel(DataclassMutableDefaultDict).dump(DataclassMutableDefaultDict()) == '{"xs": {}}'


class TestDecoder:
    def test_list(self):
        actual = JsonModel(DataclassWithList).load('{"xs": [1]}')
        expected = DataclassWithList([1])
        assert (actual == expected)

    def test_list_str(self):
        actual = JsonModel(DataclassWithListStr).load('{"xs": ["1"]}')
        expected = DataclassWithListStr(["1"])
        assert actual == expected

    def test_dict(self):
        actual = JsonModel(DataclassWithDict).load('{"kvs": {"1": "a"}}')
        expected = DataclassWithDict({'1': 'a'})
        assert actual == expected

    def test_set(self):
        actual = JsonModel(DataclassWithSet).load('{"xs": [1]}')
        expected = DataclassWithSet({1})
        assert actual == expected

    def test_tuple(self):
        actual = JsonModel(DataclassWithTuple).load('{"xs": [1, "2"]}')
        expected = DataclassWithTuple((1, "2"))
        assert actual == expected

    def test_tuple_collection(self):
        actual = JsonModel(DataclassWithTupleCollection).load('{"xs": [1, 2]}')
        expected = DataclassWithTupleCollection((1, 2))
        assert actual == expected


    def test_frozenlist(self):
        actual = JsonModel(DataclassWithFrozenList).load('{"xs": [1, 2, 3]}')
        expected = DataclassWithFrozenList(FrozenList([1, 2, 3]))
        assert actual == expected

    def test_frozenset(self):
        actual = JsonModel(DataclassWithFrozenSet).load('{"xs": [1]}')
        expected = DataclassWithFrozenSet(frozenset([1]))
        assert actual == expected

    def test_optional(self):
        actual1 = JsonModel(DataclassWithOptional).load('{"x": 1}')
        expected1 = DataclassWithOptional(1)
        assert actual1 == expected1

        actual2 = JsonModel(DataclassWithOptional).load('{"x": null}')
        expected2 = DataclassWithOptional(None)
        assert actual2 == expected2

    def test_optional_str(self):
        actual1 = JsonModel(DataclassWithOptionalStr).load('{"x": "1"}')
        expected1 = DataclassWithOptionalStr("1")
        assert actual1 == expected1

        actual2 = JsonModel(DataclassWithOptionalStr).load('{"x": null}')
        expected2 = DataclassWithOptionalStr(None)
        assert actual2 == expected2

        actual3 = JsonModel(DataclassWithOptionalStr, allow_missing=True).load('{}')
        expected3 = DataclassWithOptionalStr()
        assert actual3 == expected3

    def test_immutable_default(self):
        actual1 = JsonModel(DataclassIntImmutableDefault).load('{"x": 0}')
        expected1 = DataclassIntImmutableDefault()
        assert actual1 == expected1

    def test_mutable_default_list(self):
        expected = DataclassMutableDefaultList()

        actual1 = JsonModel(DataclassMutableDefaultList).load('{"xs": []}')
        assert actual1 == expected

        actual2 = JsonModel(DataclassMutableDefaultList, allow_missing=True).load('{}')
        assert actual2 == expected

    def test_mutable_default_dict(self):
        expected = DataclassMutableDefaultDict()

        actual1 = JsonModel(DataclassMutableDefaultDict).load('{"xs": {}}')
        assert actual1 == expected

        actual2 = JsonModel(DataclassMutableDefaultDict, allow_missing=True).load('{}')
        assert actual2 == expected
