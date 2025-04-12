from __future__ import annotations

from simple_tkinter.types import UniqueSymbolValue

from abc import abstractmethod
from uuid import UUID
from typing import (
    TYPE_CHECKING,
    Any,
    Union,
    Generic,
    TypeVar,
    Callable,
    NamedTuple,
    cast,
)
from dataclasses import field, asdict, astuple, replace, dataclass
from collections.abc import Iterable


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
    target_current: "Widget"
    target_current_is_self: bool
    target_by_id: Union["Widget", None]
    target_by_class: tuple["Widget", ...]


EventCallback = Callable[[EventCallState[ES]], Any]


class EventRegistry(dict[str, EventCallback[ES]]):
    def __init__(self, mapping: dict[str, EventCallback[ES]], *, frozen: bool = False):
        super().__init__()
        for name, func in mapping.items():
            self[name] = func
        self._frozen: bool = frozen

    def __getitem__(self, name: str):
        if self._frozen:
            raise KeyError("object is frozen and can not be modified")
        return super()[name]

    def __setitem__(self, name: str, callback: EventCallback[ES]):
        if self._frozen:
            raise KeyError("object is frozen and can not be modified")
        if not callable(callback):
            raise TypeError("event callback must be callable")
        super()[name] = callback

    def __delitem__(self, name: str):
        if self._frozen:
            raise KeyError("object is frozen and can not be modified")
        del super()[name]


class HasEvents:
    events_reserved: EventRegistry[Any]
    events: EventRegistry[Any]

    def __init__(self):
        if hasattr(self, "reserved_events"):
            self.events_reserved = EventRegistry(self.events_reserved, frozen=True)
        else:
            self.events_reserved = EventRegistry({}, frozen=True)
        if hasattr(self, "events"):
            self.events = EventRegistry(self.events)
        else:
            self.events = EventRegistry({})


@dataclass(unsafe_hash=True)
class DimensionBox:
    x: float = field(default=0)
    y: float = field(default=0)
    z: int = field(default=0)
    vec2d: tuple[float, float] = field(init=False, default=(0, 0))
    vec3d: tuple[float, float, int] = field(init=False, default=(0, 0, 0))
    vec2d_center: tuple[float, float] = field(init=False, default=(0, 0))
    vec3d_center: tuple[float, float, int] = field(init=False, default=(0, 0, 0))
    has_subpixel_position: bool = field(init=False, default=False)
    w: float = field(default=0)
    h: float = field(default=0)
    has_subpixel_size: bool = field(init=False, default=False)
    perimeter: float = field(init=False, default=0)
    area: float = field(init=False, default=0)

    def as_dict(self):
        return asdict(self)

    def as_tuple(self):
        return astuple(self)

    def copy_shallow(
        self, **changes: Union[int, float, bool, tuple[Union[int, float], ...]]
    ):
        return replace(self, **changes)

    @abstractmethod
    def overlaps(self, other: "DimensionBox") -> bool: ...

    @abstractmethod
    def covers(self, other: "DimensionBox") -> bool: ...

    @abstractmethod
    def contains(self, other: "DimensionBox") -> bool: ...

    @abstractmethod
    def inside(self, other: "DimensionBox") -> bool: ...

    @abstractmethod
    def touches(self, other: "DimensionBox") -> bool: ...


class HasPresenceInSpace:
    def will_appearance_update(self) -> bool: ...

    @abstractmethod
    def get_box_absolute(
        self,
        *,
        only_content: bool = False,
        after_appearance_update: bool = False,
        include_border: bool = True,
        include_title_bar_if_window: bool = True,
    ) -> DimensionBox: ...

    @abstractmethod
    def get_box_required(
        self,
        *,
        only_content: bool = False,
        after_appearance_update: bool = False,
        include_border: bool = True,
        include_title_bar_if_window: bool = True,
    ) -> DimensionBox: ...
