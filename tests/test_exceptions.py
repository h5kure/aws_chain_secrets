import unittest

from aws_chain_secrets.exceptions import (
    DecryptionFailureException,
    InternalServiceErrorException,
    InvalidParameterException,
    InvalidRequestException,
    ResourceNotFoundException,
    SecretsManagerException,
)


class SecretsManagerExceptionTestCase(unittest.TestCase):
    KNOWN_CODE_TO_EXCEPTION = {
        "DecryptionFailureException": DecryptionFailureException,
        "InternalServiceErrorException": InternalServiceErrorException,
        "InvalidParameterException": InvalidParameterException,
        "InvalidRequestException": InvalidRequestException,
        "ResourceNotFoundException": ResourceNotFoundException,
    }
    UNKNOWN_CODE = "UnknownCode"

    def test_base_exception_uses_default_message_when_message_is_none(self):
        self.assertEqual("Unknown error occurred.", str(SecretsManagerException()))

    def test_base_exception_uses_given_message(self):
        self.assertEqual("custom message", str(SecretsManagerException("custom message")))

    def test_from_code_maps_each_known_code_to_its_subclass(self):
        for code, exception_class in self.KNOWN_CODE_TO_EXCEPTION.items():
            with self.subTest(code=code):
                self.assertIs(exception_class, type(SecretsManagerException.from_code(code)))

    def test_from_code_returns_base_class_for_unknown_code(self):
        self.assertIs(SecretsManagerException, type(SecretsManagerException.from_code(self.UNKNOWN_CODE)))

    def test_from_code_passes_message_to_exception(self):
        for code in (*self.KNOWN_CODE_TO_EXCEPTION, self.UNKNOWN_CODE):
            with self.subTest(code=code):
                self.assertEqual("aws message", str(SecretsManagerException.from_code(code, "aws message")))

    def test_subclasses_are_secrets_manager_exceptions(self):
        for exception_class in self.KNOWN_CODE_TO_EXCEPTION.values():
            with self.subTest(exception_class=exception_class.__name__):
                self.assertTrue(issubclass(exception_class, SecretsManagerException))

    def test_invalid_parameter_exception_uses_default_message_string(self):
        message = "You provided an invalid value for a parameter."
        self.assertEqual(message, InvalidParameterException.DEFAULT_MESSAGE)
        self.assertEqual(message, str(InvalidParameterException()))
