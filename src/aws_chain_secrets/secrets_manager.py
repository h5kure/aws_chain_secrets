import json
from collections import ChainMap
from collections.abc import ItemsView, KeysView, ValuesView
from typing import Any

from botocore.exceptions import ClientError

from aws_chain_secrets.caster import cast
from aws_chain_secrets.client import Client
from aws_chain_secrets.exceptions import SecretsManagerException


class Null:
    """
    class to represent null type
    """


null = Null()


class SecretsManager(Client):
    def __init__(
        self,
        region_name: str,
        *secret_names: str,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
    ):
        """
        initial setup
        :param region_name: AWS region name
        :param secret_names: The secret names that come later has higher precedence..
        :raises ValueError: if no secret name is given
        """
        if not secret_names:
            raise ValueError("At least one secret name is required.")
        self.secret_names = secret_names
        super().__init__("secretsmanager", region_name, aws_access_key_id, aws_secret_access_key)
        self._secrets: dict[str, dict[str, Any]] = {secret_name: {} for secret_name in secret_names}
        self._combined = ChainMap(*reversed(self._secrets.values()))

    def get(self, key: str, *, default: Any = null, casting_type: type[Any] = str):
        """
        get secret value
        :param key: key value to search
        :param default: default value if key not exists in secrets
        :param casting_type: casting type to convert value
        :return: Any secret value specified by key
        """
        try:
            value = self._combined[key]
        except KeyError:
            if isinstance(default, Null):
                raise KeyError(f"{key!r} not found. Please check secret value in AWS Secrets Manager.") from None
            return default
        return cast(value, casting_type)

    def set(self, secret_name: str | None, key: str, value) -> None:
        """
        set a `key: value` to the specified secret
        :param secret_name: secret_name of AWS Secrets Manager.
         If `None` is given, the value is set to the highest priority secret (last given as a parameter) with key value.
         If there is no secret with the given key,
          it is registered as a new value in the secret with the highest priority.
        :param key: key of map
        :param value: value of map
        """
        if secret_name is None:
            secret_name = self._find_secret_name_for(key)
        self._secrets[secret_name][key] = value

    def keys(self) -> KeysView[str]:
        return self._combined.keys()

    def values(self) -> ValuesView[Any]:
        return self._combined.values()

    def items(self) -> ItemsView[str, Any]:
        return self._combined.items()

    def fetch(self) -> None:
        """
        get secrets from AWS and update
        """
        for secret_name in self.secret_names:
            self._secrets[secret_name].clear()
            self._secrets[secret_name].update(self._get_secrets(secret_name))

    def update(self, secret_name: str | None = None) -> None:
        """
        update specified secrets from local to AWS
        :param secret_name: secret name of AWS Secrets Manager. If `None` is given, updates the entire secrets.
        """
        if secret_name is None:
            for name in self._secrets:
                self.update(name)
        else:
            # BaseClient has no typed service methods.
            self._connected_client().update_secret(  # type: ignore[attr-defined]
                SecretId=secret_name, SecretString=json.dumps(self._secrets[secret_name])
            )

    def _find_secret_name_for(self, key: str) -> str:
        """
        find the secret that `set(None, key, value)` writes to
        :param key: key of map
        :return: the highest priority secret containing key, otherwise the highest priority secret.
        """
        names = list(reversed(self._secrets))
        return next((name for name in names if key in self._secrets[name]), names[0])

    def _get_secrets(self, secret_name: str) -> dict[str, Any]:
        """
        get secrets from AWS
        :param secret_name: secret name of AWS Secrets Manager
        """
        client = self._connected_client()
        try:
            # BaseClient has no typed service methods.
            response = client.get_secret_value(SecretId=secret_name)  # type: ignore[attr-defined]
        except ClientError as e:
            error = e.response["Error"]
            raise SecretsManagerException.from_code(error["Code"], error.get("Message")) from e
        else:
            if "SecretString" in response:
                return json.loads(response["SecretString"])
            return json.loads(response["SecretBinary"])

    __call__ = get

    def __enter__(self) -> "SecretsManager":
        super().__enter__()
        self.fetch()
        return self
