import boto3
from botocore.client import BaseClient


class Client:
    """
    wrapper for AWS client
    """

    def __init__(
        self,
        service_name: str,
        region_name: str,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
    ):
        self.service_name = service_name
        self.region_name = region_name
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self._client: BaseClient | None = None

    def connect(self) -> None:
        self._client = self._create_client()

    def disconnect(self) -> None:
        if self._client is None:
            return
        self._client.close()
        self._client = None

    def _create_client(self) -> BaseClient:
        # Client serves any service, so service_name is a plain str; the stubs only accept literal names.
        return boto3.session.Session().client(  # type: ignore[call-overload]
            service_name=self.service_name,
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        )

    def __enter__(self) -> "Client":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
