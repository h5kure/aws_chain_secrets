class SecretsManagerException(Exception):
    DEFAULT_MESSAGE = "Unknown error occurred."

    def __init__(self, message: str | None = None):
        super().__init__(message or self.DEFAULT_MESSAGE)

    @classmethod
    def from_code(cls, code: str, message: str | None = None) -> "SecretsManagerException":
        if code == "DecryptionFailureException":
            return DecryptionFailureException(message)
        elif code == "InternalServiceErrorException":
            return InternalServiceErrorException(message)
        elif code == "InvalidParameterException":
            return InvalidParameterException(message)
        elif code == "InvalidRequestException":
            return InvalidRequestException(message)
        elif code == "ResourceNotFoundException":
            return ResourceNotFoundException(message)
        else:
            return cls(message)


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
