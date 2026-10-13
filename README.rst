AWS chain secrets
===================

This package aims to make using AWS SecretsManager more comfortable.

Introduce
---------
This aims to enable the use of one or more secrets from AWS SecretsManager.

If more than one secret is used, the secret specified last takes precedence.

For example, if you use secrets named A and B in that order, overlapping entries from A and B will later use
the value of the specified B entry.


.. code-block:: python

    >>> A = {"foo": 1, "bar": 2}
    >>> B = {"bar": 3}
    >>> secrets("bar", casting_type=int)
    3

Install
-------

Python 3.10 or later is required.

.. code-block:: bash

    $ python -m pip install aws_chain_secrets


How to use
----------

.. note::

    AWS credential is required.

    If your credentials installed or set to environment, you can omit credentials when initialize `SecretsManager`.

    Each secret must hold a JSON object, either as `SecretString` or as `SecretBinary` (raw bytes).

connect and fetch manually
""""""""""""""""""""""""""

.. code-block:: python

    from aws_chain_secrets import SecretsManager
    secrets = SecretsManager('ap-northeast-2', 'secret_name_1', 'secret_name_2', ...)
    secrets.connect()
    secrets.fetch()
    secrets(key="A", default=None, casting_type=int)
    secrets.disconnect()

At least one secret name is required; `SecretsManager` raises `ValueError` without one.

`fetch()` and `update()` need a connection and raise `RuntimeError` without one.
`get()` and `set()` only work on local values, so they work without a connection.


.. note::

    The secret assigned last takes precedence over secrets assigned earlier.

    In this case, `secret_name_2` has a higher priority than `secret_name_1`.

    This works likes `dict.update` (`secret_name_1.update(secret_name_2)`).

use with context manager
""""""""""""""""""""""""

You can omit `connect()`, `fetch()` and `disconnect()` when using context manager.

.. code-block:: python

    from aws_chain_secrets import SecretsManager
    with SecretsManager('ap-northeast-2', 'secret_name_1', 'secret_name_2', ...) as secrets:
        secrets(key="A", default=None, casting_type=int)

type casting
""""""""""""

All secret values ​​retrieved from AWS SecretsManager are string types by default.

You can change it to any type you want.

.. code-block:: python

    >>> secrets(key="A", casting_type=int)
    1
    >>> secrets(key="SOME_ARRAY", casting_type=list)
    ['1', '2', '3', '4']
    >>> secrets(key="SOME_ARRAY", casting_type=list[int])
    [1, 2, 3, 4]

default value
"""""""""""""

You can specify a default value, just like when using Python `dict`'s `get`.

.. code-block:: python

    # if the key value of A does not exist, 0 specified as default is returned.
    >>> secrets(key="A", default=0)
    0

change value
""""""""""""

You can change (or add) the value of a specified secret by name.

If `None` is given, the value is set to the highest priority secret (last given as a parameter) with key value.

If there is no secret with the given key, it is registered as a new value in the secret with the highest priority.

.. code-block:: python

    >>> secrets.set('secret_name_1', 'key', 'value')

update remote (AWS secrets manager) data from local
"""""""""""""""""""""""""""""""""""""""""""""""""""

You can update (upload) the values of a specified secret by name from local to remote.

If `None` is given (if the parameter is omitted), the entire secrets are updated.

.. code-block:: python

    >>> secrets.update('secret_name_1')
