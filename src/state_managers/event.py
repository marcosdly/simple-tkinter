from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Final,
    Mapping,
    TypeVar,
    Callable,
    Hashable,
    MutableSet,
    Reversible,
)
from functools import partial
from collections.abc import Sequence


if TYPE_CHECKING:
    from src.widget import WidgetLike

EventCallback = Callable[[WidgetLike, str, dict[str, Any], Callable[[], None]], None]

_T = TypeVar("_T")


class Event(MutableSet[EventCallback], Sequence, Reversible, Hashable):
    name: str
    widget: "WidgetLike"
    __owner_event_map: dict[str, Event]

    def __init__(
        self,
        *,
        name: str,
        event_widget_target: "WidgetLike",
        owner_event_map: dict[str, Event],
    ):
        self.name = name
        self.widget = event_widget_target
        self.__owner_event_map = owner_event_map
        self.__values: tuple[EventCallback, ...] = ()

    def emit(self, data: dict[str, Any]) -> None:
        for func in self.__values:
            func(self.widget, self.name, data, partial(self.discard, func))

    def __getitem__(self, index: int) -> EventCallback:
        return self.__values.__getitem__(index)

    def __contains__(self, item: object) -> bool:
        return self.__values.__contains__(item)

    def __iter__(self):
        return self.__values.__iter__()

    def __len__(self) -> int:
        return self.__values.__len__()

    def __reversed__(self):
        return self.__values.__reversed__()

    def __hash__(self) -> int:
        return hash((self.name, self.widget))

    def add(self, func: EventCallback) -> None:
        i = len(self.__values)
        if func not in self.__values:
            self.__values += (func,)
        if i == 0:
            self.__owner_event_map[self.name] = self

    def discard(self, func: EventCallback) -> None:
        self.__values = tuple(v for v in self.__values if v is not func)
        if len(self.__values) == 0:
            _ = self.__owner_event_map.pop(self.name, None)

    def index(
        self, func: EventCallback, start: int = 0, stop: int | None = None
    ) -> int:
        return self.__values.index(func, start, stop or len(self.__values))

    def clear(self) -> None:
        self.__values = ()
        _ = self.__owner_event_map.pop(self.name, None)

    def pop(self) -> EventCallback:
        if len(self.__values) == 0:
            raise KeyError("pop from an empty Event")
        value = self.__values[-1]
        self.__values = self.__values[:-1]
        if len(self.__values) == 0:
            _ = self.__owner_event_map.pop(self.name, None)
        return value


class EventMapping(Mapping[str, Event], Hashable):
    __event_map: dict[str, Event]
    widget: "WidgetLike"

    __magic_const_hash_factor: Final[int] = 0x5F3759DF
    """
    Magic int to help avoid hash collisions.

    Made constant (hard-coded) to ensure consistent hashing accross arbitrary cases.

    """

    def __hash__(self) -> int:
        return hash((self.widget, self.__magic_const_hash_factor))

    def __init__(self, event_widget_target: "WidgetLike"):
        self.__event_map = {}
        self.widget = event_widget_target

    def __getitem__(self, key: str) -> Event:
        if key not in self.__event_map:
            return Event(
                name=key,
                event_widget_target=self.widget,
                owner_event_map=self.__event_map,
            )
        return self.__event_map[key]

    def __iter__(self):
        return self.__event_map.__iter__()

    def __len__(self) -> int:
        return self.__event_map.__len__()

    def __contains__(self, key: object) -> bool:
        return self.__event_map.__contains__(key)

    def __eq__(self, other: object) -> bool:
        return self.__event_map.__eq__(other)

    def __ne__(self, other: object) -> bool:
        return self.__event_map.__ne__(other)

    def keys(self):
        return self.__event_map.keys()

    def items(self):
        return self.__event_map.items()

    def values(self):
        return self.__event_map.values()

    def get(self, key: str, default: _T | None = None) -> Event | _T | None:
        return self.__event_map.get(key, default)


class Mixin_WithEvent:
    """
    Usage:

    class MyWidget(Widget, Mixin_WithEvent):
        def _define_events(self) -> None:
            self.event["click"] = self.on_click

            @self.event["hover"]
            def on_hover(widget: WidgetLike, event_name: str, event_info: dict[str, Any]) -> None:
                ...

    """

    event: EventMapping

    def __init__(self, *args, event_widget_target: "WidgetLike", **kwargs):
        super().__init__(*args, **kwargs)
        self.event = EventMapping(event_widget_target)
        self._define_base_events()

    def _define_base_events(self) -> None: ...
