from __future__ import annotations
from queue import Queue
from typing import ClassVar, TypedDict, Union


STYLE_UPDATE_QUEUE = Queue()


_StyleValueType = Union[int, float, str, bool, tuple, list, dict]


class _StyleAnnotation(TypedDict):
    name: str
    type: _StyleValueType
    default: _StyleValueType | None


class WithStyle:
    """Mixin class to add style management capabilities to widgets."""

    __style_annotations__: ClassVar[dict[str, _StyleAnnotation]] | None = None
    """Style type and parser annotations for this widget-like class."""
    __style_prev_hash: int
    __style_curr_hash: int
    """Hash of the current style dictionary."""
    __style: dict[str, _StyleValueType]
    """Internal style dictionary."""

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls, *args, **kwargs)
        self.__style_prev_hash = 0
        self.__style_curr_hash = 0
        self.__style = {}
        return self

    def __getattribute__(self, name: str) -> object:
        if name == "style":
            STYLE_UPDATE_QUEUE.put(self)
            return super().__getattribute__("__style")
        return super().__getattribute__(name)

    def __check_and_update_style_hash(self) -> None:
        """Compute hash of the style dictionary. If the has changed since last call, update the previous and current hash attributes."""
        style = getattr(self, "__style", None)
        if style is None or len(style) == 0:
            _hash = 0
        else:
            _hash = hash(tuple(sorted(style.values(), key=str)))
        self.__style_prev_hash = self.__style_curr_hash
        self.__style_curr_hash = _hash

    def is_style_changed(self) -> bool:
        """Check if the style has changed since last hash update."""
        self.__check_and_update_style_hash()
        return self.__style_curr_hash != self.__style_prev_hash
