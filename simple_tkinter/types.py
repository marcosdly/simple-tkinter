from __future__ import annotations

from uuid import uuid4
from typing import Any

class _UniqueSymbolValue_ClassAsValue(type):
    _hash_value: int
    _name: str

    def __new__(cls, name:str, bases:tuple[type,...], namespace:dict[str, Any], **kwds: Any)->type[UniqueSymbolValue]:
        self: type = type(name, bases, namespace, **kwds)
        self._hash_value = uuid4().int
        self._name = name
        return self

    def __eq__(self, other: Any):
        return other is self

    def __hash__(self) -> int:
        return self._hash_value

    def __repr__(self) -> str:
        return f"<UniqueSymbolValue '{self._name}' hash 0x{self._hash_value:X}>"

    def __setattr__(self, name: str, value: Any) -> None:
        raise NotImplementedError

    def __setitem__(self, name: str, value: Any) -> None:
        raise NotImplementedError

    def __getitem__(self, name: str) -> None:
        raise NotImplementedError


class UniqueSymbolValue(metaclass=_UniqueSymbolValue_ClassAsValue): ...
