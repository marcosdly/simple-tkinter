from __future__ import annotations

from uuid import UUID
from typing import TYPE_CHECKING, Union


if TYPE_CHECKING:
    from simple_tkinter.widget import Widget


class App:
    def __init__(self):
        self._widget_instance_id_registry: dict[UUID, "Widget"] = {}
        self._widget_style_id_registry: dict[str, "Widget"] = {}
        self._widget_style_class_registry: dict[str, list["Widget"]]

    def find_by_instance_id(self, _uuid: UUID) -> Union["Widget", None]:
        return self._widget_instance_id_registry.get(_uuid, None)

    def find_by_id(self, _id: str) -> Union["Widget", None]:
        return self._widget_style_id_registry.get(_id, None)

    def find_by_class(self, _class: str) -> tuple["Widget", ...]:
        return tuple(self._widget_style_class_registry.get(_class, []))
