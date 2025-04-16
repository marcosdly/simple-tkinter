from __future__ import annotations

import copy

from uuid import uuid4
from typing import Any, TypeVar, Callable, Hashable, Optional, final
from collections.abc import Mapping, Sequence


class _UniqueSymbolValue_ClassAsValue(type):
    _hash_value: int
    _name: str

    def __new__(
        cls, name: str, bases: tuple[type, ...], namespace: dict[str, Any], **kwds: Any
    ) -> type[UniqueSymbolValue]:
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


KT = TypeVar("KT", bound=Hashable)
VT = TypeVar("VT")

EventfulSimpleDictCallback = Callable[[KT, Optional[VT], Optional[VT]], Any]


@final
class EventfulSimpleDict(Mapping[KT, VT]):
    def __init__(
        self,
        init_mapping: Optional[Mapping[KT, VT]] = None,
        *,
        slots: Optional[Sequence[KT]] = None,
        on_setitem_pre: Optional[EventfulSimpleDictCallback[KT, VT]] = None,
        on_setitem_post: Optional[EventfulSimpleDictCallback[KT, VT]] = None,
    ):
        self._data: dict[KT, VT] = {}
        if init_mapping is not None:
            self._data.update(init_mapping)
        self._on_setitem_pre = on_setitem_pre
        self._on_setitem_post = on_setitem_post
        self.slots = tuple(slots) if slots is not None else None

    def __getitem__(self, key: KT):
        if self.slots is not None and key not in self.slots:
            raise KeyError(f"unknown key {repr(key)}")
        return self._data.__getitem__(key)

    def __setitem__(self, key: KT, value: VT):
        if self.slots is not None and key not in self.slots:
            raise KeyError(f"unknown key {repr(key)}")
        previous_value = self._data.get(key, None)
        if self._on_setitem_pre is not None:
            self._on_setitem_pre(key, previous_value, value)
        self._data.__setitem__(key, value)
        if self._on_setitem_post is not None:
            self._on_setitem_post(key, previous_value, value)

    def __iter__(self):
        return self._data.__iter__()

    def __len__(self):
        return self._data.__len__()

    def __contains__(self, key: KT):
        return self._data.__contains__(key)

    def __eq__(self, other: Any):
        return self._data.__eq__(other)

    def __ne__(self, other: Any):
        return self._data.__eq__(other)

    def keys(self):
        return self._data.keys()

    def items(self):
        return self._data.items()

    def values(self):
        return self._data.values()

    def get(self, key: KT, default: Optional[VT] = None):
        return self._data.get(key, default)

    def copy(self):
        return self._data.copy()

    def deepcopy(self):
        return copy.deepcopy(self._data)
