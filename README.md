# AWS chain secrets

[![PyPI](https://img.shields.io/pypi/v/aws_chain_secrets)](https://pypi.org/project/aws_chain_secrets/)
[![Python](https://img.shields.io/pypi/pyversions/aws_chain_secrets)](https://pypi.org/project/aws_chain_secrets/)
[![CI](https://github.com/h5kure/aws_chain_secrets/actions/workflows/ci.yml/badge.svg)](https://github.com/h5kure/aws_chain_secrets/actions/workflows/ci.yml)
[![License](https://img.shields.io/pypi/l/aws_chain_secrets)](https://github.com/h5kure/aws_chain_secrets/blob/main/LICENSE)

Read several AWS Secrets Manager secrets as one key-value store.
When the same key appears in more than one secret, the secret given last wins.

## Quick start

Suppose these two secrets are stored in AWS Secrets Manager.

`myapp/common`:

```json
{"DB_HOST": "db.internal", "DB_PORT": "5432", "DEBUG": "false"}
```

`myapp/prod`:

```json
{"DB_HOST": "prod-db.internal"}
```

```python
from aws_chain_secrets import SecretsManager

with SecretsManager("ap-northeast-2", "myapp/common", "myapp/prod") as secrets:
    secrets("DB_HOST")  # 'prod-db.internal' (myapp/prod wins)
    secrets("DB_PORT", casting_type=int)  # 5432 (only in myapp/common)
    secrets("DEBUG", casting_type=bool)  # False
```

## Install

Python 3.10 or later is required.

```bash
python -m pip install aws_chain_secrets
```

## Secret format

Each secret must hold a JSON object, stored either as `SecretString` or as `SecretBinary` (the raw JSON bytes).

Values can be any JSON type. They are returned as stored, with the matching Python type:

| Stored value | `secrets(key)` returns |
|---|---|
| `"5432"` | `'5432'` |
| `5432` | `5432` |
| `false` | `False` |
| `null` | `None` |
| `[1, 2]` | `[1, 2]` |
| `{"a": 1}` | `{'a': 1}` |

The AWS console's key/value editor stores every value as a string.
Use [Type casting](#type-casting) to convert such strings, for example `"5432"` to `5432`.

## Usage

### Precedence

Secret names are given in order of increasing priority, so a later secret overrides an earlier one.
It works like `ChainMap(later, earlier)`, or like applying `dict.update` from the first secret to the last.

### Connecting

As a context manager, `SecretsManager` connects and fetches every secret on entry and disconnects on exit.

```python
with SecretsManager("ap-northeast-2", "myapp/common", "myapp/prod") as secrets:
    ...
```

You can also manage the connection yourself:

```python
secrets = SecretsManager("ap-northeast-2", "myapp/common", "myapp/prod")
secrets.connect()
secrets.fetch()
...
secrets.disconnect()
```

At least one secret name is required. `fetch()` and `update()` need a connection;
reading and changing local values with `get()` and `set()` do not.

### Reading values

`secrets(key)` is a shorthand for `secrets.get(key)`. Both take keyword-only `default` and `casting_type`.

```python
secrets.get("DB_HOST")  # 'prod-db.internal'
secrets("TIMEOUT", default=30)  # 30 when TIMEOUT is missing
secrets("TIMEOUT", default=30, casting_type=int)
```

- A missing key without `default` raises `KeyError`.
- `default` is returned as is; `casting_type` is not applied to it.
- `keys()`, `values()` and `items()` return a merged view of all secrets.
- Without `casting_type`, a list or dict is the stored object itself, not a copy,
  so changing it changes the local secret that `update()` uploads.
  Pass `casting_type=list` or `casting_type=dict` for a copy.

### Type casting

Pass `casting_type` to convert a value.

A string value is parsed:

| `casting_type` | Stored value | Result |
|---|---|---|
| `int`, `float`, or any type that takes a string | `"5432"` | `5432` |
| `bool` | `"true"`, `"yes"`, `"on"`, `"1"`, ... | `True` |
| | `"false"`, `"no"`, `"off"`, `"0"`, `""`, ... | `False` |
| `list`, `set`, `tuple` | `"a, b, c"` | `['a', 'b', 'c']` |
| `list[int]`, `set[int]`, `tuple[int]` | `"1, 2, 3"` | `[1, 2, 3]` |
| `dict` | `"{\"a\": 1}"` | `{'a': 1}` |

- `bool` is case-insensitive and raises `ValueError` for any other string.
- Sequences are split on `,` and each item is stripped of surrounding whitespace.

Any other JSON value is converted with `casting_type(value)`, as Python does:

| `casting_type` | Stored value | Result |
|---|---|---|
| `int` | `3.5` | `3` |
| `bool` | `5432` | `True` |
| | `0`, `null` | `False` |
| `list`, `set`, `tuple` | `[1, "a"]` | `[1, 'a']` |
| `dict` | `{"a": 1}` | `{'a': 1}` (a copy) |
| `str` | `false` | `'False'` |

- Generic sequences such as `list[int]` cast each item by these rules, so `["1", 2]` gives `[1, 2]`.
- `str` uses Python's `str()`, not JSON spelling. For JSON text, use `json.dumps(secrets(key))`.
- Other generic types, such as `dict[str, int]`, raise `NotImplementedError`.

### Changing values

`set()` changes a value locally. It does not touch AWS until you call `update()`.

```python
secrets.set("myapp/common", "DB_PORT", "6432")  # write to a specific secret
secrets.set(None, "DB_HOST", "new-db.internal")  # let the library choose
```

With `None`, the value goes to the highest-priority secret that already has the key,
or to the highest-priority secret if none has it. An unknown secret name raises `KeyError`.

`fetch()` reloads every secret from AWS and discards local changes.

### Writing values to AWS

`update()` uploads local values with `UpdateSecret`.

```python
secrets.update("myapp/common")  # one secret
secrets.update()  # every secret, in the order given
```

> **Warning:** `update()` replaces the whole secret with the local values as JSON `SecretString`.
> It does not merge, so changes made in AWS since your last `fetch()` are lost.
> A secret stored as `SecretBinary` is written back as `SecretString`.

## Errors

| Error | When |
|---|---|
| `ValueError` | `SecretsManager` is created without a secret name |
| `RuntimeError` | `fetch()` or `update()` is called without a connection |
| `KeyError` | `get()` misses a key without `default`, or `set()` gets an unknown secret name |
| `aws_chain_secrets.exceptions.SecretsManagerException` | `fetch()` fails in AWS |

`fetch()` converts AWS errors to `SecretsManagerException` or one of its subclasses,
keeping the original `botocore.exceptions.ClientError` as `__cause__`:
`DecryptionFailureException`, `InternalServiceErrorException`, `InvalidParameterException`,
`InvalidRequestException` and `ResourceNotFoundException`.
Other codes, such as `AccessDeniedException`, become `SecretsManagerException` itself.
`update()` raises the `ClientError` unchanged.

## AWS credentials and permissions

Credentials come from the default boto3 chain: environment variables, the shared credentials file, or an IAM role.
You can pass keys instead:

```python
SecretsManager(
    "ap-northeast-2",
    "myapp/common",
    aws_access_key_id="...",
    aws_secret_access_key="...",
)
```

Named profiles and session tokens cannot be passed directly; set them through the environment (`AWS_PROFILE`, `AWS_SESSION_TOKEN`).

Required IAM permissions:

- `secretsmanager:GetSecretValue` for `fetch()`
- `secretsmanager:UpdateSecret` for `update()`
- `kms:Decrypt` (and `kms:GenerateDataKey` for `update()`) when a secret uses a customer managed KMS key

## Changelog

See [CHANGELOG.md](https://github.com/h5kure/aws_chain_secrets/blob/main/CHANGELOG.md).

## Development

```bash
uv sync
uv run pytest
uv run ruff check
uv run ruff format --check
uv run mypy
```

## License

[MIT](https://github.com/h5kure/aws_chain_secrets/blob/main/LICENSE)
