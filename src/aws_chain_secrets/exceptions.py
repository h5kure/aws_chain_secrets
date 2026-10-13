class SecretsManagerException(Exception):
    DEFAULT_MESSAGE = "Unknown error occurred."

    def __init__(self, message: str | None = None):
        super().__init__(message or self.DEFAULT_MESSAGE)

    @classmethod
    def from_code(cls, code: str, message: str | None = None) -> "SecretsManagerException":
        return _EXCEPTION_BY_CODE.get(code, cls)(message)


class DecryptionFailureException(SecretsManagerException):
    DEFAULT_MESSAGE = "Secrets Manager can't decrypt the protected secret text using the provided KMS key."


class InternalServiceErrorException(SecretsManagerException):
    DEFAULT_MESSAGE = "An error occurred on the server side."


class InvalidParameterException(SecretsManagerException):
    DEFAULT_MESSAGE = "You provided an invalid value for a parameter."


class InvalidRequestException(SecretsManagerException):
    DEFAULT_MESSAGE = "You provided a parameter value that is not valid for the current state of the resource."


class ResourceNotFoundException(SecretsManagerException):
    DEFAULT_MESSAGE = "We can't find the resource that you asked for."


# AWS error codes with a dedicated exception; any other code becomes the class from_code is called on.
_EXCEPTION_BY_CODE = {
    "DecryptionFailureException": DecryptionFailureException,
    "InternalServiceErrorException": InternalServiceErrorException,
    "InvalidParameterException": InvalidParameterException,
    "InvalidRequestException": InvalidRequestException,
    "ResourceNotFoundException": ResourceNotFoundException,
}
