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

Pass a type, or a function that takes the value, as `casting_type` to convert a value.
The result is `casting_type(value)`, as in Python, with two exceptions for strings
where Python would give a wrong value without an error:

- `bool`: `bool("false")` is `True`, so a string is read as a truth value instead.
- Sequences: `list("a,b")` gives `['a', ',', 'b']`, so a string is split on `,` instead.

For any other conversion, such as reading JSON text, pass a function.

A string value:

| `casting_type` | Stored value | Result |
|---|---|---|
| `bool` | `"true"`, `"yes"`, `"on"`, `"1"`, ... | `True` |
| | `"false"`, `"no"`, `"off"`, `"0"`, `""`, ... | `False` |
| `list`, `set`, `frozenset`, `tuple` | `"a, b, c"` | `['a', 'b', 'c']` |
| `list[int]`, `set[int]`, `frozenset[int]`, `tuple[int, ...]` | `"1, 2, 3"` | `[1, 2, 3]` |
| any of the above sequences | `""`, `"  "` | `[]` (empty) |
| `tuple[str, int]` | `"db, 5432"` | `('db', 5432)` |
| `int`, `float`, or any other type that takes a string | `"5432"` | `5432` |
| `dict` | `"{\"a\": 1}"` | `ValueError`, as from `dict()` |
| `bytes`, `bytearray` | `"hi"` | `TypeError`, as from `bytes()` |

- `bool` ignores case and surrounding whitespace, so `" True "` gives `True` and `"  "` gives `False`.
  It raises `ValueError` for any other string.
- Sequences are split on `,` and each item is stripped of surrounding whitespace.
  Empty items are kept: `"a,,b"` gives `['a', '', 'b']` and `"a,b,"` gives `['a', 'b', '']`.
- A generic tuple casts by position, as in typing. `tuple[str, int]` takes exactly two items
  and `tuple[int]` exactly one; another number of items raises `ValueError`.
  Use `tuple[int, ...]` for any number of items.
- An empty or whitespace-only string gives an empty sequence, the same as a JSON `[]`.
  The AWS console stores a cleared value as `""`. Other types get the string as is:
  `int` and `float` raise `ValueError`, and a function or a type such as `pathlib.Path` receives `""`.

Any other JSON value:

| `casting_type` | Stored value | Result |
|---|---|---|
| `int` | `3.5` | `3` |
| `bool` | `5432` | `True` |
| | `0`, `null` | `False` |
| `list`, `set`, `frozenset`, `tuple` | `[1, "a"]` | `[1, 'a']` |
| `dict` | `{"a": 1}` | `{'a': 1}` (a copy) |
| `bytes` | `[104, 105]` | `b'hi'` |
| | `5` | `b'\x00\x00\x00\x00\x00'` (five zero bytes) |
| `str` | `false` | `'False'` |

- Generic sequences such as `list[int]` cast each item by these rules, so `["1", 2]` gives `[1, 2]`.
- `str` uses Python's `str()`, not JSON spelling. For JSON text, use `json.dumps(secrets(key))`.
- `bytes` and `bytearray` treat a number as a length, so store bytes as a list of integers,
  or as text read with a function below.
- Other generic types, such as `dict[str, int]`, raise `NotImplementedError`.

A function is called with the stored value as is.
A comma-separated string reads with `list`, while JSON text such as `"[1, 2]"` or `"{\"a\": 1}"` reads with `json.loads`:

```python
import base64
import json

secrets("FEATURES", casting_type=json.loads)  # '{"beta": true}' -> {'beta': True}
secrets("SIGNING_KEY", casting_type=str.encode)  # "héllo" -> b'h\xc3\xa9llo'
secrets("TLS_KEY", casting_type=base64.b64decode)  # "aGk=" -> b'hi'
secrets("API_SALT", casting_type=bytes.fromhex)  # "6869" -> b'hi'
```

For a sequence with another delimiter, pass `Sequence` from `aws_chain_secrets.caster`:

```python
from aws_chain_secrets.caster import Sequence

secrets("PORTS", casting_type=Sequence(cast_type=int, delimiter=";"))  # "80; 443" -> [80, 443]
secrets("TAGS", casting_type=Sequence(cast_type=str.lower, wrapper=set))  # "A, b" -> {'a', 'b'}
```

Its fields are keyword-only:

- `cast_type`: a type, or a function, for each item, cast by the rules above. Default `str`.
- `delimiter`: the string to split on. Default `","`.
- `strip`: characters stripped from both ends of each item. Default whitespace.
- `wrapper`: the container type, such as `list`, `set`, `frozenset` or `tuple`. Default `list`.

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
| `aws_chain_secrets.SecretsManagerException` | `fetch()` fails in AWS |

`fetch()` converts AWS errors to `SecretsManagerException` or one of its subclasses,
keeping the original `botocore.exceptions.ClientError` as `__cause__`:
`DecryptionFailureException`, `InternalServiceErrorException`, `InvalidParameterException`,
`InvalidRequestException` and `ResourceNotFoundException`.
Other codes, such as `AccessDeniedException`, become `SecretsManagerException` itself.
`update()` raises the `ClientError` unchanged.

The exceptions can be imported from `aws_chain_secrets`:

```python
from aws_chain_secrets import ResourceNotFoundException

try:
    secrets.fetch()
except ResourceNotFoundException:
    ...
```

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
