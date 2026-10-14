# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- `casting_type` accepts a function that takes the value, such as `json.loads`, `str.encode` or `base64.b64decode`.
  It is called with the stored value as is. Type annotations now allow it.

### Changed
- Python 3.10 or later is required.
- `set(None, key, value)` writes to the highest-priority secret that has `key`.
  Previously it wrote to the lowest-priority one, so `get(key)` kept returning the old value.
- `SecretsManagerException.from_code()` raises `TypeError` for an unhashable `code`.
- `SecretsManager()` raises `ValueError` when no secret name is given.
  Previously it could be created, and `set(None, ...)` then failed with `KeyError(None)`.
  **Affected:** code that creates `SecretsManager` with an empty list of secret names.
  **Migration:** pass at least one secret name, or skip creating `SecretsManager` when there is none.
- Exceptions converted from an AWS `ClientError` keep it as `__cause__`.
- The `KeyError` from `get()` no longer shows the internal lookup error as its context.
- `SecretBinary` is parsed as the raw bytes boto3 returns. Previously it was base64-decoded a second time,
  so a binary secret stored with boto3 as plain JSON bytes failed with `binascii.Error`.
  **Affected:** binary secrets that hold base64 text, for example stored with `SecretBinary=base64.b64encode(...)`
  or with AWS CLI v1 `--secret-binary "<base64>"`. Reading them now fails with `ValueError`.
  **Migration:** store the JSON bytes themselves as `SecretBinary`, or store the JSON as `SecretString`.
- `casting_type` converts a value that is not a JSON string with `casting_type(value)`, as Python does.
  Strings are cast as before, except with `dict` (see below). `bool` follows Python truthiness for such values:
  `5432` gives `True` and `null` gives `False`, where both raised `ValueError` before.
  **Affected:** code that relied on that `ValueError` from `casting_type=bool` for a non-string value.
  **Migration:** check the value yourself before casting, or store the flag as a string such as `"true"`.
- `get()` and `secrets(key)` return the stored value as is by default (`casting_type=None`).
  Previously the default was `casting_type=str`, so a value that is not a JSON string came back in Python spelling,
  for example `'5432'`, `'False'` or `"{'a': 1}"`. String values are unchanged.
  A list or dict is now the stored object itself, as with `values()`.
  **Affected:** code that reads a non-string value without `casting_type` and expects a string,
  for example the numeric `port` of a secret managed by Amazon RDS.
  **Migration:** pass `casting_type=str`, or use the value with its JSON type.
- `casting_type=list`, `set`, `frozenset`, `tuple` and generic sequences such as `list[int]`
  return an empty container for an empty or whitespace-only string, as for a JSON `[]`.
  The AWS console stores a cleared value as `""`. Previously sequences gave one empty item such as `['']`
  and generic sequences raised `ValueError`.
  **Affected:** code that expects `['']` for a cleared value, or catches that error to detect it.
  **Migration:** treat an empty container as unset, or read the value with `casting_type=None` and check for `""`.
- `casting_type=dict` no longer parses a string as JSON. It passes the string to `dict()` as Python does,
  which raises `ValueError`. Previously a JSON string was parsed, so `'[1, 2]'` gave a list instead of a dict.
  **Affected:** code that reads a JSON object stored as a string with `casting_type=dict`.
  **Migration:** pass `casting_type=json.loads`.
- `casting_type=bool` ignores surrounding whitespace in a string, so `" true "` gives `True`
  and a whitespace-only string gives `False` like `""`. Previously both raised `ValueError`.
- A generic tuple casts by position, as in typing: `tuple[str, int]` casts `"db, 5432"` to `('db', 5432)`,
  and the number of items must match, so `tuple[int]` takes exactly one item.
  Another number of items raises `ValueError`. `tuple[int, ...]` casts any number of items, including none.
  Previously every item was cast with the first type argument, whatever the number of items.
  **Affected:** code that uses `tuple[int]` or `tuple[int, str]` for a list of any length.
  **Migration:** use `tuple[int, ...]` for any number of items of one type.

### Removed
- `aws_chain_secrets.caster.cast_boolean()`. It converted any value with `str()` before reading it as a truth value.
  **Migration:** use `casting_type=bool` for a string value.

### Fixed
- `InvalidParameterException()` has a string default message instead of a tuple.
- Exceptions converted from an AWS `ClientError` carry the AWS error message.
- `Client.disconnect()` can be called more than once, and before `connect()`.
- The wheel no longer installs a top-level `tests` package.
- `fetch()` and `update()` raise `RuntimeError` without a connection,
  instead of an `AttributeError` about `NoneType`.
- `casting_type=list`, `set`, `tuple` and generic sequences such as `list[int]` convert JSON arrays,
  casting each item for generic sequences. Previously they failed with `AttributeError`.
- `casting_type=dict` returns a copy of a JSON object. Previously it failed with `TypeError`.
- `casting_type=frozenset` and `frozenset[int]` split a string value on `,` like `set`.
  Previously `frozenset` split it into characters and `frozenset[int]` raised `NotImplementedError`.
