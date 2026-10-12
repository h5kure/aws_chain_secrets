import unittest

from aws_chain_secrets.client import Client


class ClientTestCase(unittest.TestCase):
    SERVICE_NAME = 'secretsmanager'
    REGION_NAME = 'ap-northeast-2'
    AWS_ACCESS_KEY_ID = 'testing-access-key'
    AWS_SECRET_ACCESS_KEY = 'testing-secret-key'

    def setUp(self):
        self.client = Client(
            self.SERVICE_NAME,
            self.REGION_NAME,
            aws_access_key_id=self.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY,
        )

    def test_client_is_none_before_connect(self):
        self.assertIsNone(self.client._client)

    def test_connect_creates_client_for_given_service_and_region(self):
        self.client.connect()
        self.addCleanup(self.client.disconnect)

        meta = self.client._client.meta
        self.assertEqual(self.SERVICE_NAME, meta.service_model.service_name)
        self.assertEqual(self.REGION_NAME, meta.region_name)

    def test_connect_passes_explicit_credentials(self):
        self.client.connect()
        self.addCleanup(self.client.disconnect)

        # botocore has no public API to read a client's credentials, so this relies on an internal attribute.
        credentials = self.client._client._request_signer._credentials
        self.assertEqual(self.AWS_ACCESS_KEY_ID, credentials.access_key)
        self.assertEqual(self.AWS_SECRET_ACCESS_KEY, credentials.secret_key)

    def test_context_manager_connects_on_enter_and_returns_self(self):
        with self.client as entered:
            self.assertIs(self.client, entered)
            self.assertIsNotNone(self.client._client)

    # This behavior is the root cause of B3. The expectation may change when B3 is fixed.
    def test_context_manager_removes_client_on_exit(self):
        with self.client:
            pass

        self.assertFalse(hasattr(self.client, '_client'))

    # KNOWN BUG(B3): to be fixed in stage 4. _client is None before connect, so close() cannot be called.
    def test_disconnect_before_connect_currently_raises_attribute_error(self):
        with self.assertRaises(AttributeError):
            self.client.disconnect()

    # KNOWN BUG(B3): to be fixed in stage 4. The first disconnect() deletes the _client attribute.
    def test_second_disconnect_currently_raises_attribute_error(self):
        self.client.connect()
        self.client.disconnect()

        with self.assertRaises(AttributeError):
            self.client.disconnect()
