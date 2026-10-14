import base64
import json
import unittest
from unittest.mock import patch

import boto3
from botocore.exceptions import ClientError
from botocore.stub import Stubber

from aws_chain_secrets import SecretsManager
from aws_chain_secrets.caster import Sequence
from aws_chain_secrets.exceptions import (
    ResourceNotFoundException,
    SecretsManagerException,
)


class SecretsManagerTestCase(unittest.TestCase):
    REGION_NAME = "ap-northeast-2"

    def setUp(self):
        self.boto_client = boto3.session.Session().client(
            "secretsmanager",
            region_name=self.REGION_NAME,
            aws_access_key_id="testing",
            aws_secret_access_key="testing",
        )
        self.stubber = Stubber(self.boto_client)
        self.stubber.activate()
        self.addCleanup(self.stubber.deactivate)

        patcher = patch.object(SecretsManager, "_create_client", return_value=self.boto_client)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _stub_secret_string(self, secret_name: str, secret: dict):
        self.stubber.add_response(
            "get_secret_value",
            {"SecretString": json.dumps(secret)},
            {"SecretId": secret_name},
        )

    def _stub_secret_binary(self, secret_name: str, secret_binary: bytes):
        self.stubber.add_response(
            "get_secret_value",
            {"SecretBinary": secret_binary},
            {"SecretId": secret_name},
        )

    def _stub_client_error(self, secret_name: str, code: str, message: str = "AWS error message"):
        self.stubber.add_client_error(
            "get_secret_value",
            service_error_code=code,
            service_message=message,
            expected_params={"SecretId": secret_name},
        )

    def _expect_update(self, secret_name: str, secret: dict):
        self.stubber.add_response(
            "update_secret",
            {},
            {"SecretId": secret_name, "SecretString": json.dumps(secret)},
        )

    def _assert_update_sends(self, secrets: SecretsManager, expected_secrets_by_name: dict[str, dict]):
        """Assert that update() sends exactly the given secrets, in the given order."""
        for secret_name, secret in expected_secrets_by_name.items():
            self._expect_update(secret_name, secret)
        secrets.update()
        self.stubber.assert_no_pending_responses()

    def _enter(self, secrets_by_name: dict[str, dict]) -> SecretsManager:
        """Stub every secret in the given order, then enter a SecretsManager over them."""
        for secret_name, secret in secrets_by_name.items():
            self._stub_secret_string(secret_name, secret)
        secrets = SecretsManager(self.REGION_NAME, *secrets_by_name)
        secrets.__enter__()
        self.addCleanup(secrets.__exit__, None, None, None)
        return secrets

    def test_enter_fetches_secret_string_as_json(self):
        self._stub_secret_string("app", {"host": "localhost", "port": "5432"})

        with SecretsManager(self.REGION_NAME, "app") as secrets:
            self.assertEqual({"host": "localhost", "port": "5432"}, dict(secrets.items()))

    def test_enter_fetches_every_secret_in_given_order(self):
        self._stub_secret_string("base", {"a": "1"})
        self._stub_secret_string("override", {"b": "2"})

        with SecretsManager(self.REGION_NAME, "base", "override"):
            self.stubber.assert_no_pending_responses()

    def test_later_secret_takes_precedence_over_earlier(self):
        secrets = self._enter({"base": {"key": "base"}, "override": {"key": "override"}})

        self.assertEqual("override", secrets.get("key"))

    def test_get_falls_back_to_lower_priority_secret(self):
        secrets = self._enter({"base": {"base_only": "base"}, "override": {"key": "override"}})

        self.assertEqual("base", secrets.get("base_only"))

    def test_get_raises_key_error_when_key_missing_and_no_default(self):
        secrets = self._enter({"app": {}})

        with self.assertRaises(KeyError) as context:
            secrets.get("missing")
        self.assertEqual(
            "'missing' not found. Please check secret value in AWS Secrets Manager.",
            context.exception.args[0],
        )

    def test_get_key_error_suppresses_internal_lookup_error(self):
        secrets = self._enter({"app": {}})

        with self.assertRaises(KeyError) as context:
            secrets.get("missing")
        self.assertIsNone(context.exception.__cause__)
        self.assertTrue(context.exception.__suppress_context__)

    def test_get_returns_default_when_key_missing(self):
        secrets = self._enter({"app": {}})

        self.assertEqual("fallback", secrets.get("missing", default="fallback"))

    def test_get_returns_none_default_when_default_is_none(self):
        secrets = self._enter({"app": {}})

        self.assertIsNone(secrets.get("missing", default=None))

    def test_get_does_not_cast_default(self):
        secrets = self._enter({"app": {}})

        self.assertEqual("1", secrets.get("missing", default="1", casting_type=int))

    def test_get_casts_value_with_casting_type(self):
        secrets = self._enter({"app": {"port": "5432"}})

        self.assertEqual(5432, secrets.get("port", casting_type=int))

    def test_get_with_sequence_uses_its_delimiter(self):
        secrets = self._enter({"app": {"ports": "1; 2"}})

        self.assertEqual([1, 2], secrets.get("ports", casting_type=Sequence(cast_type=int, delimiter=";")))

    def test_get_returns_stored_value_by_default(self):
        secrets = self._enter({"app": {"host": "localhost", "port": 5432, "debug": False}})

        self.assertEqual("localhost", secrets.get("host"))
        self.assertEqual(5432, secrets.get("port"))
        self.assertIs(False, secrets.get("debug"))

    def test_get_returns_stored_list_itself(self):
        secrets = self._enter({"app": {"hosts": ["a", "b"]}})

        self.assertIs(next(iter(secrets.values())), secrets.get("hosts"))

    def test_call_is_alias_of_get(self):
        secrets = self._enter({"app": {"host": "localhost", "port": "5432"}})

        self.assertEqual("localhost", secrets("host"))
        self.assertEqual(5432, secrets("port", casting_type=int))
        self.assertEqual("fallback", secrets("missing", default="fallback"))

    def test_keys_values_items_reflect_combined_view(self):
        secrets = self._enter(
            {
                "base": {"base_only": "base", "key": "base"},
                "override": {"key": "override", "port": 5432},
            }
        )

        self.assertEqual(["base_only", "key", "port"], list(secrets.keys()))
        self.assertEqual(["base", "override", 5432], list(secrets.values()))
        self.assertEqual([("base_only", "base"), ("key", "override"), ("port", 5432)], list(secrets.items()))

    # botocore already base64-decodes blob fields, so SecretBinary arrives as raw bytes.
    def test_secret_binary_raw_bytes_are_parsed_as_json(self):
        self._stub_secret_binary("app", b'{"host": "localhost"}')

        with SecretsManager(self.REGION_NAME, "app") as secrets:
            self.assertEqual({"host": "localhost"}, dict(secrets.items()))

    def test_secret_binary_holding_base64_text_is_no_longer_decoded(self):
        self._stub_secret_binary("app", base64.b64encode(b'{"host": "localhost"}'))

        with self.assertRaises(ValueError):
            with SecretsManager(self.REGION_NAME, "app"):
                pass

    def test_fetch_replaces_local_values_with_remote(self):
        secrets = self._enter({"app": {"key": "remote-v1"}})
        secrets.set("app", "key", "local")
        self._stub_secret_string("app", {"key": "remote-v2"})

        secrets.fetch()

        self.assertEqual("remote-v2", secrets.get("key"))

    def test_fetch_removes_keys_deleted_remotely(self):
        secrets = self._enter({"app": {"kept": "1", "deleted": "2"}})
        self._stub_secret_string("app", {"kept": "1"})

        secrets.fetch()

        self.assertEqual(["kept"], list(secrets.keys()))

    def test_fetch_before_connect_raises_runtime_error(self):
        secrets = SecretsManager(self.REGION_NAME, "app")

        with self.assertRaises(RuntimeError) as context:
            secrets.fetch()
        self.assertEqual(
            "SecretsManager is not connected; call connect() or use it as a context manager.",
            str(context.exception),
        )

    def test_client_error_is_converted_to_mapped_exception(self):
        self._stub_client_error("app", "ResourceNotFoundException")

        with self.assertRaises(SecretsManagerException) as context:
            with SecretsManager(self.REGION_NAME, "app"):
                pass
        self.assertIs(ResourceNotFoundException, type(context.exception))

    def test_client_error_is_chained_as_cause(self):
        self._stub_client_error("app", "ResourceNotFoundException")

        with self.assertRaises(ResourceNotFoundException) as context:
            with SecretsManager(self.REGION_NAME, "app"):
                pass
        self.assertIsInstance(context.exception.__cause__, ClientError)

    def test_unknown_client_error_code_becomes_base_exception(self):
        self._stub_client_error("app", "AccessDeniedException")

        with self.assertRaises(SecretsManagerException) as context:
            with SecretsManager(self.REGION_NAME, "app"):
                pass
        self.assertIs(SecretsManagerException, type(context.exception))

    def test_client_error_message_is_passed_to_exception(self):
        self._stub_client_error("app", "ResourceNotFoundException", message="Secrets Manager can't find 'app'.")

        with self.assertRaises(ResourceNotFoundException) as context:
            with SecretsManager(self.REGION_NAME, "app"):
                pass
        self.assertEqual("Secrets Manager can't find 'app'.", str(context.exception))

    def test_exit_disconnects_client(self):
        self._stub_secret_string("app", {})

        with SecretsManager(self.REGION_NAME, "app") as secrets:
            pass

        self.assertIsNone(secrets._client)

    def test_update_with_secret_name_sends_that_secret_as_json(self):
        secrets = self._enter({"base": {"a": "1"}, "override": {"b": "2"}})
        self._expect_update("override", {"b": "2"})

        secrets.update("override")

        self.stubber.assert_no_pending_responses()

    def test_update_none_sends_every_secret(self):
        secrets = self._enter({"base": {"a": "1"}, "override": {"b": "2"}})

        self._assert_update_sends(secrets, {"base": {"a": "1"}, "override": {"b": "2"}})

    def test_update_after_exit_raises_runtime_error(self):
        self._stub_secret_string("app", {"a": "1"})
        with SecretsManager(self.REGION_NAME, "app") as secrets:
            pass

        with self.assertRaises(RuntimeError) as context:
            secrets.update("app")
        self.assertEqual(
            "SecretsManager is not connected; call connect() or use it as a context manager.",
            str(context.exception),
        )

    def test_set_with_secret_name_writes_to_that_secret(self):
        secrets = self._enter({"base": {"key": "base"}, "override": {"key": "override"}})

        secrets.set("base", "key", "changed")

        self._assert_update_sends(secrets, {"base": {"key": "changed"}, "override": {"key": "override"}})

    def test_set_with_unknown_secret_name_raises_key_error(self):
        secrets = self._enter({"app": {}})

        with self.assertRaises(KeyError):
            secrets.set("unknown", "key", "value")

    def test_set_none_writes_to_highest_priority_when_key_absent(self):
        secrets = self._enter({"base": {"a": "1"}, "override": {"b": "2"}})

        secrets.set(None, "new", "value")

        self._assert_update_sends(secrets, {"base": {"a": "1"}, "override": {"b": "2", "new": "value"}})

    def test_set_none_writes_to_only_secret_containing_key(self):
        secrets = self._enter({"base": {"key": "base"}, "override": {"b": "2"}})

        secrets.set(None, "key", "changed")

        self._assert_update_sends(secrets, {"base": {"key": "changed"}, "override": {"b": "2"}})

    def test_set_none_with_key_in_multiple_secrets_writes_highest_priority(self):
        secrets = self._enter({"base": {"key": "base"}, "override": {"key": "override"}})

        secrets.set(None, "key", "changed")

        self.assertEqual("changed", secrets.get("key"))
        self._assert_update_sends(secrets, {"base": {"key": "base"}, "override": {"key": "changed"}})

    def test_constructor_without_secret_names_raises_value_error(self):
        with self.assertRaises(ValueError) as context:
            SecretsManager(self.REGION_NAME)
        self.assertEqual("At least one secret name is required.", str(context.exception))
