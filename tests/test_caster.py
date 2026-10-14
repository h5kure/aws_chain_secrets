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

    # KNOWN BUG(B8): a JSON array is not a string, so splitting it fails.
    def test_cast_json_array_to_list_currently_raises_attribute_error(self):
        for casting_type in (list, set, tuple):
            with self.subTest(casting_type=casting_type), self.assertRaises(AttributeError):
                caster.cast([1, "a"], casting_type)

    # KNOWN BUG(B8): a JSON array is not a string, so splitting it fails.
    def test_cast_json_array_to_generic_list_currently_raises_attribute_error(self):
        with self.assertRaises(AttributeError):
            caster.cast(["1", 2], list[int])

    # KNOWN BUG(B8): a JSON object is not a string, so json.loads fails.
    def test_cast_json_object_to_dict_currently_raises_type_error(self):
        with self.assertRaises(TypeError):
            caster.cast({"a": 1}, dict)

    # KNOWN BUG(B8): non-string values are judged by the truth strings of their str().
    def test_cast_non_string_to_bool_currently_uses_truth_strings(self):
        for value in (5432, None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                caster.cast(value, bool)
        self.assertIs(True, caster.cast(1, bool))
        self.assertIs(True, caster.cast(True, bool))

    def test_cast_non_string_float_to_int_truncates(self):
        self.assertEqual(3, caster.cast(3.5, int))

    def test_cast_non_string_to_str_uses_python_str(self):
        self.assertEqual("False", caster.cast(False, str))
        self.assertEqual("{'a': 1}", caster.cast({"a": 1}, str))
