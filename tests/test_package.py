import unittest

import aws_chain_secrets
from aws_chain_secrets import exceptions


class PackageTestCase(unittest.TestCase):
    def test_package_exports_public_api(self):
        self.assertEqual(
            {
                "SecretsManager",
                "SecretsManagerException",
                "DecryptionFailureException",
                "InternalServiceErrorException",
                "InvalidParameterException",
                "InvalidRequestException",
                "ResourceNotFoundException",
            },
            set(aws_chain_secrets.__all__),
        )
        from aws_chain_secrets import ResourceNotFoundException

        self.assertIs(exceptions.ResourceNotFoundException, ResourceNotFoundException)
