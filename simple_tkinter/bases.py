from __future__ import annotations

from uuid import UUID
from typing import TYPE_CHECKING, Union, cast, NamedTuple, TypeVar, Generic, Any, Callable
from collections.abc import Iterable
from simple_tkinter.types import UniqueSymbolValue


if TYPE_CHECKING:
    from simple_tkinter.app import App
    from simple_tkinter.widget import Widget


WidgetTree = dict["Widget", Union["Widget", Iterable["Widget"], "WidgetTree"]]


class HasChildren:
    def __init__(self):
        self.parent: Union["App", "Widget"]
        self.app: "App"
        self._widget_instance_id_registry: dict[UUID, "Widget"] = {}
        self._widget_style_id_registry: dict[str, "Widget"] = {}
        self._widget_style_class_registry: dict[str, list["Widget"]]
        self._children: list["Widget"] = []

    def find_by_instance_id(self, _uuid: UUID) -> Union["Widget", None]:
        return self._widget_instance_id_registry.get(_uuid, None)

    def find_by_id(self, _id: str) -> Union["Widget", None]:
        return self._widget_style_id_registry.get(_id, None)

    def find_by_class(self, _class: str) -> tuple["Widget", ...]:
        return tuple(self._widget_style_class_registry.get(_class, []))

    def get_children(self):
        return tuple(self._children)

    def append_child(self, widget: "Widget"):
        self._widget_instance_id_registry[widget.instance_id] = widget
        # safer access to App instance since widgets always have the self.app reference
        widget.app.append_child(widget)
        if widget.parent is self:
            self._children.append(widget)

    def append_children_tree(self, widget_tree: WidgetTree):
        if not len(widget_tree):
            return

        from simple_tkinter.widget import Widget

        for widget, tree_descriptor in widget_tree.items():
            self.append_child(widget)
            if isinstance(tree_descriptor, dict):
                # recursion
                self.append_children_tree(cast(WidgetTree, tree_descriptor))
                continue
            if isinstance(tree_descriptor, Widget):
                self.append_child(tree_descriptor)
                continue
            _iterable = ()
            try:
                _iterable = iter(tree_descriptor)
            except TypeError as err:
                raise TypeError(
                    "widget tree expected to be iterable but is not"
                ) from err
            for sub_widget in _iterable:
                self.append_child(sub_widget)

ES = TypeVar("ES", bound=NamedTuple)

class EventValueUnknown(UniqueSymbolValue): ...

class EventCallState(Generic[ES], NamedTuple):
    event_name: str
    event_global_count: int
    event_data: Union[EventValueUnknown, Any]
    event_state: ES
    caller_widget: "Widget"
    target_current:"Widget"
    target_current_is_self: bool
    target_by_id: Union["Widget", None]
    target_by_class: tuple["Widget", ...]

EventCallback = Callable[[EventCallState[ES]], Any]

class EventRegistry(dict[str, EventCallback[ES]]):
    def __init__(self, mapping: dict[str, EventCallback[ES]], *, frozen:bool=False):
        super().__init__()
        for name, func in mapping.items():
            self[name] = func
        self._frozen: bool = frozen

    def __getitem__(self, name: str):
        if self._frozen:
            raise KeyError('object is frozen and can not be modified')
        return super()[name]

    def __setitem__(self, name: str, callback: EventCallback[ES]):
        if self._frozen:
            raise KeyError('object is frozen and can not be modified')
        if not callable(callback):
            raise TypeError('event callback must be callable')
        super()[name] = callback

    def __delitem__(self, name: str):
        if self._frozen:
            raise KeyError('object is frozen and can not be modified')
        del super()[name]

class HasEvents:
    events_reserved: EventRegistry[Any]
    events: EventRegistry[Any]

    def __init__(self):
        if hasattr(self, "reserved_events"):
            self.events_reserved = EventRegistry(self.events_reserved, frozen=True)
        else:
            self.events_reserved = EventRegistry({}, frozen=True)
        if hasattr(self,"events"):
            self.events = EventRegistry(self.events)
        else:
            self.events = EventRegistry({})

