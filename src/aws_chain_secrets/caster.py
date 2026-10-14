import string
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from types import GenericAlias
from typing import Any, get_args, get_origin

TRUE_STRINGS = ("y", "yes", "t", "true", "on", "1")
FALSE_STRINGS = ("", "n", "no", "f", "false", "off", "0")
_SEQUENCE_TYPES = (set, frozenset, list, tuple)


def string_to_boolean(value: str) -> bool:
    """
    Convert a string representation of truth to True or False.
    Case and surrounding whitespace are ignored.

    :param value: a string representation of truth
    :return: True if value represents truth, False if value represents false, otherwise raise ValueError
    :raises: Raises ValueError if 'value' is anything else
    """
    value = value.strip().lower()
    if value in TRUE_STRINGS:
        return True
    if value in FALSE_STRINGS:
        return False
    raise ValueError(f"invalid truth value {value!r}")


def cast_boolean(value: Any) -> bool:
    value = str(value)
    return string_to_boolean(value)


def cast(value: Any, casting_type: Callable[[Any], Any] | GenericAlias | None = None) -> Any:
    """
    secret value to typed value
    :param value: original value. A string is parsed; any other value is converted with `casting_type(value)`.
     Generic sequences such as `list[int]` cast each item the same way.
    :param casting_type: a type, or a function that takes the value such as `base64.b64decode`.
     `None` returns the value as is.
    :return: typed value
    """
    if casting_type is None:
        return value
    if isinstance(casting_type, GenericAlias):
        origin = get_origin(casting_type)
        args = get_args(casting_type)
        if origin in _SEQUENCE_TYPES:
            return Sequence(cast_type=args[0] if args else str, wrapper=origin)(value)
        raise NotImplementedError(f"cannot cast to {casting_type!r}")
    if not isinstance(value, str):
        return casting_type(value)
    if casting_type is bool:
        return cast_boolean(value)
    if casting_type in _SEQUENCE_TYPES:
        return Sequence(wrapper=casting_type)(value)
    return casting_type(value)


@dataclass
class Sequence:
    """
    Helper to cast Sequence (list, tuple) and Set(set, frozenset)
    from a delimited string or from an iterable of items.
    A blank string gives an empty container.
    """

    cast_type: Callable[[Any], Any] | GenericAlias = str
    delimiter: str = ","
    strip: str = string.whitespace
    wrapper: type[Any] = list

    def __call__(self, value: str | Iterable[Any]):
        if isinstance(value, str):
            parts = value.split(self.delimiter) if value.strip(self.strip) else []
            value = (v.strip(self.strip) for v in parts)
        return self.wrapper(cast(item, self.cast_type) for item in value)
