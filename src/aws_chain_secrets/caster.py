import json
import string
from dataclasses import dataclass
from types import GenericAlias
from typing import Any, Type, get_origin, get_args

TRUE_STRINGS = ('y', 'yes', 't', 'true', 'on', '1')
FALSE_STRINGS = ('', 'n', 'no', 'f', 'false', 'off', '0')


def string_to_boolean(value: str) -> bool:
    """
    Convert a string representation of truth to True or False.

    :param value: a string representation of truth
    :return: True if value represents truth, False if value represents false, otherwise raise ValueError
    :raises: Raises ValueError if 'value' is anything else
    """
    value = value.lower()
    if value in TRUE_STRINGS:
        return True
    if value in FALSE_STRINGS:
        return False
    raise ValueError(f"invalid truth value {repr(value)}")


def cast_boolean(value: Any) -> bool:
    value = str(value)
    return string_to_boolean(value)


def cast(value: str, casting_type: Type = None) -> Any:
    """
    string value to typed value
    :param value: original string
    :param casting_type: expected type to be
    :return: typed value
    """
    if casting_type is None:
        return value
    if casting_type is bool:
        return cast_boolean(value)
    if casting_type in (set, list, tuple, bytes, bytearray):
        return Sequence(wrapper=casting_type)(value)
    if casting_type is dict:
        return json.loads(value)
    if isinstance(casting_type, GenericAlias):
        origin = get_origin(casting_type)
        args = get_args(casting_type)
        if origin in (set, list, tuple, bytes, bytearray):
            return Sequence(cast_type=args[0] if args else str, wrapper=origin)(value)
        raise NotImplementedError(f"cannot cast to {repr(casting_type)}")
    return casting_type(value)


@dataclass
class Sequence:
    """
    Helper to cast Sequence (list, tuple, bytes, bytearray) and Set(set, frozenset)
    """
    cast_type: Type = str
    delimiter: str = ','
    strip: str = string.whitespace
    wrapper: Type = list

    def __call__(self, value: str):
        return self.wrapper(cast(v.strip(self.strip), self.cast_type) for v in value.split(self.delimiter))
