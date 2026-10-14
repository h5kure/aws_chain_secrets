import unittest

from aws_chain_secrets import caster


class CasterTestCase(unittest.TestCase):
    def test_int(self):
        self.assertEqual(1, caster.cast("1", int))

    def test_bool(self):
        self.assertTrue(caster.cast("true", bool))

    def test_list(self):
        self.assertEqual(["1", "2", "3", "4"], caster.cast("1,2,3,4", list))
        self.assertEqual([1, 2, 3, 4], caster.cast("1, 2, 3, 4", list[int]))

    def test_set(self):
        self.assertEqual({1, 2, 3, 4}, caster.cast("1,2,3,4", set[int]))

    def test_dict(self):
        self.assertEqual({"foo": "bar"}, caster.cast('{"foo": "bar"}', dict))

    def test_cast_json_array_to_list_converts_it(self):
        for casting_type in (list, set, frozenset, tuple):
            with self.subTest(casting_type=casting_type):
                self.assertEqual(casting_type([1, "a"]), caster.cast([1, "a"], casting_type))

    def test_cast_json_array_to_bytes_converts_it(self):
        for casting_type in (bytes, bytearray):
            with self.subTest(casting_type=casting_type):
                self.assertEqual(b"hi", caster.cast([104, 105], casting_type))

    def test_cast_json_array_to_generic_list_casts_each_item(self):
        self.assertEqual([1, 2], caster.cast(["1", 2], list[int]))

    def test_cast_json_object_to_dict_returns_copy(self):
        value = {"a": 1}

        result = caster.cast(value, dict)

        self.assertEqual(value, result)
        self.assertIsNot(value, result)

    def test_cast_non_string_to_bool_uses_python_truthiness(self):
        for value, expected in ((5432, True), (True, True), (0, False), (None, False)):
            with self.subTest(value=value):
                self.assertIs(expected, caster.cast(value, bool))

    def test_cast_non_string_float_to_int_truncates(self):
        self.assertEqual(3, caster.cast(3.5, int))

    def test_cast_non_string_to_str_uses_python_str(self):
        self.assertEqual("False", caster.cast(False, str))
        self.assertEqual("{'a': 1}", caster.cast({"a": 1}, str))

    # KNOWN BUG(B9): bytes is treated as a container, so it becomes bytes(["hi"]).
    def test_cast_string_to_bytes_currently_raises_type_error(self):
        for casting_type in (bytes, bytearray):
            with self.subTest(casting_type=casting_type), self.assertRaises(TypeError):
                caster.cast("hi", casting_type)

    # KNOWN BUG(B10): frozenset is not in the sequence types, so frozenset("a,b") splits it into characters.
    def test_cast_string_to_frozenset_currently_splits_into_characters(self):
        self.assertEqual(frozenset({"a", ",", "b"}), caster.cast("a,b", frozenset))

    # KNOWN BUG(B10): frozenset is not in the generic sequence types.
    def test_cast_string_to_generic_frozenset_currently_raises_not_implemented_error(self):
        with self.assertRaises(NotImplementedError):
            caster.cast("1,2", frozenset[int])
