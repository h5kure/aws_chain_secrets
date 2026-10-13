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
