import string
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from types import GenericAlias
from typing import Any, get_args, get_origin

TRUE_STRINGS = ("y", "yes", "t", "true", "on", "1")
FALSE_STRINGS = ("", "n", "no", "f", "false", "off", "0")
_SEQUENCE_TYPES = (set, frozenset, list, tuple)
_DELIMITER = ","
_STRIP = string.whitespace


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


def cast(value: Any, casting_type: Callable[[Any], Any] | GenericAlias | None = None) -> Any:
    """
    Convert a secret value with `casting_type(value)`, as Python does.
    A string is the exception for two types where Python gives a wrong value without an error:
    `bool` reads TRUE_STRINGS and FALSE_STRINGS, since `bool("false")` is True,
    and sequences split on `,`, since `list("a,b")` gives characters.
    Pass a function such as `json.loads` for any other conversion.
    :param value: stored value
    :param casting_type: a type, or a function that takes the value. `None` returns the value as is.
     Generic sequences such as `list[int]` cast each item by the same rules.
     A generic tuple casts by position as in typing: `tuple[str, int]` takes exactly two items,
     `tuple[int, ...]` any number.
    :return: typed value
    """
    if casting_type is None:
        return value
    if isinstance(casting_type, GenericAlias):
        origin = get_origin(casting_type)
        args = get_args(casting_type)
        if origin is tuple and args[1:] != (Ellipsis,):
            return _cast_by_position(value, args)
        if origin in _SEQUENCE_TYPES:
            return Sequence(cast_type=args[0] if args else str, wrapper=origin)(value)
        raise NotImplementedError(f"cannot cast to {casting_type!r}")
    if isinstance(value, str):
        if casting_type is bool:
            return string_to_boolean(value)
        if casting_type in _SEQUENCE_TYPES:
            return Sequence(wrapper=casting_type)(value)
    return casting_type(value)


@dataclass(kw_only=True)
class Sequence:
    """
    A `casting_type` that builds `wrapper` from a delimited string or from an iterable of items,
    casting each item with `cast_type` by the rules of `cast()`.
    A string is split on `delimiter` and each item is stripped of the characters in `strip`.
    A blank string gives an empty container.
    """

    cast_type: Callable[[Any], Any] | GenericAlias = str
    delimiter: str = _DELIMITER
    strip: str = _STRIP
    wrapper: type[Any] = list

    def __call__(self, value: str | Iterable[Any]):
        items = _split_items(value, self.delimiter, self.strip)
        return self.wrapper(cast(item, self.cast_type) for item in items)


def _split_items(value: str | Iterable[Any], delimiter: str, strip: str) -> Iterable[Any]:
    """
    Split a string on `delimiter` and strip each item; a blank string gives no items.
    Any other iterable is returned as is.
    """
    if isinstance(value, str):
        parts = value.split(delimiter) if value.strip(strip) else []
        return (part.strip(strip) for part in parts)
    return value


def _cast_by_position(value: str | Iterable[Any], item_types: tuple[Any, ...]) -> tuple[Any, ...]:
    items = list(_split_items(value, _DELIMITER, _STRIP))
    if len(items) != len(item_types):
        raise ValueError(f"expected {len(item_types)} tuple item(s), got {len(items)}")
    return tuple(cast(item, item_type) for item, item_type in zip(items, item_types, strict=True))
