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
    def test_base_exception_uses_default_message_when_message_is_none(self):
        self.assertEqual("Unknown error occurred.", str(SecretsManagerException()))

    def test_base_exception_uses_given_message(self):
        self.assertEqual("custom message", str(SecretsManagerException("custom message")))

    def test_from_code_maps_each_known_code_to_its_subclass(self):
        expected = {
            'DecryptionFailureException': DecryptionFailureException,
            'InternalServiceErrorException': InternalServiceErrorException,
            'InvalidParameterException': InvalidParameterException,
            'InvalidRequestException': InvalidRequestException,
            'ResourceNotFoundException': ResourceNotFoundException,
        }
        for code, exception_class in expected.items():
            with self.subTest(code=code):
                self.assertIs(exception_class, type(SecretsManagerException.from_code(code)))

    def test_from_code_returns_base_class_for_unknown_code(self):
        self.assertIs(SecretsManagerException, type(SecretsManagerException.from_code('UnknownCode')))

    def test_from_code_passes_message_to_exception(self):
        codes = (
            'DecryptionFailureException',
            'InternalServiceErrorException',
            'InvalidParameterException',
            'InvalidRequestException',
            'ResourceNotFoundException',
            'UnknownCode',
        )
        for code in codes:
            with self.subTest(code=code):
                self.assertEqual("aws message", str(SecretsManagerException.from_code(code, "aws message")))

    def test_subclasses_are_secrets_manager_exceptions(self):
        subclasses = (
            DecryptionFailureException,
            InternalServiceErrorException,
            InvalidParameterException,
            InvalidRequestException,
            ResourceNotFoundException,
        )
        for exception_class in subclasses:
            with self.subTest(exception_class=exception_class.__name__):
                self.assertTrue(issubclass(exception_class, SecretsManagerException))

    # KNOWN BUG(B1): 4단계에서 수정. DEFAULT_MESSAGE 끝의 쉼표 때문에 문자열이 아니라 tuple이다.
    def test_invalid_parameter_default_message_is_currently_a_tuple(self):
        message = "You provided an invalid value for a parameter."
        self.assertEqual((message,), InvalidParameterException.DEFAULT_MESSAGE)
        self.assertEqual(str((message,)), str(InvalidParameterException()))
