import base64
import json
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

    def test_cast_string_to_dict_raises_value_error(self):
        for value in ('{"foo": "bar"}', "[1, 2]", "  "):
            with self.subTest(value=value), self.assertRaises(ValueError):
                caster.cast(value, dict)

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

    def test_cast_string_to_bytes_raises_type_error(self):
        for casting_type in (bytes, bytearray):
            with self.subTest(casting_type=casting_type), self.assertRaises(TypeError):
                caster.cast("hi", casting_type)

    def test_cast_string_to_frozenset_splits_it(self):
        self.assertEqual(frozenset({"a", "b"}), caster.cast("a, b", frozenset))

    def test_cast_string_to_generic_frozenset_casts_each_item(self):
        self.assertEqual(frozenset({1, 2}), caster.cast("1,2", frozenset[int]))

    def test_cast_with_function_applies_it(self):
        self.assertEqual(b"hi", caster.cast("aGk=", base64.b64decode))
        self.assertEqual(b"hi", caster.cast("6869", bytes.fromhex))
        self.assertEqual({"a": 1}, caster.cast('{"a": 1}', json.loads))
        self.assertEqual(b"h\xc3\xa9llo", caster.cast("héllo", str.encode))

    def test_cast_blank_string_to_sequence_returns_empty_container(self):
        for casting_type, expected in (
            (list, []),
            (set, set()),
            (frozenset, frozenset()),
            (tuple, ()),
            (list[int], []),
            (set[int], set()),
            (frozenset[int], frozenset()),
            (tuple[int], ()),
        ):
            for value in ("", "  ", "\t\n"):
                with self.subTest(casting_type=casting_type, value=value):
                    result = caster.cast(value, casting_type)

                    self.assertEqual(expected, result)
                    self.assertIs(type(expected), type(result))

    def test_cast_empty_string_to_number_raises_value_error(self):
        for casting_type in (int, float):
            with self.subTest(casting_type=casting_type), self.assertRaises(ValueError):
                caster.cast("", casting_type)

    def test_cast_string_with_empty_items_keeps_them(self):
        self.assertEqual(["a", "", "b"], caster.cast("a,,b", list))
        self.assertEqual(["a", "b", ""], caster.cast("a,b,", list))

    def test_sequence_with_blank_string_returns_empty_container(self):
        self.assertEqual([], caster.Sequence(cast_type=int, delimiter=";")("  "))
        self.assertEqual([], caster.Sequence(strip=" -")("--"))
