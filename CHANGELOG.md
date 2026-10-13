# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

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

### Fixed
- `InvalidParameterException()` has a string default message instead of a tuple.
- Exceptions converted from an AWS `ClientError` carry the AWS error message.
- `Client.disconnect()` can be called more than once, and before `connect()`.
- The wheel no longer installs a top-level `tests` package.
- `fetch()` and `update()` raise `RuntimeError` without a connection,
  instead of an `AttributeError` about `NoneType`.
