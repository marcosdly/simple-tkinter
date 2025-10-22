from __future__ import annotations

import src.python_meta as py

from typing import Any


__all__ = [
    "is_instance_registered",
    "get_registered_instance_id",
    "register_instance_id",
]


_REGISTRY_ADDR2ID: dict[int, int] = {}
"""Registry mapping instance memory ids to unique object references."""

_REGISTRY_ID2REF: dict[int, object] = {}
"""Registry mapping unique object references to instance references."""

_REGISTRY_WINDOW2WIDGET_COUNT: dict[int, int] = {}
"""Registry mapping Window ids to their number of registered Widgets."""

IdHierarchy = dict[int, "IdHierarchy|None"]

_REGISTRY_ID_HIERARCHY: IdHierarchy = {}
"""Registry mapping instance ids to their hierarchical structure a.k.a children."""

_WINDOW_ID_COUNTER: int = 0
"""
Counter for assigning unique Window ids.

Not to be in any way related to: the number of Windows registered, the order of
registration, it's position in the children hierarchy.

"""

_BIT_OFFSET = 32


def _python_hash_registry_object(registry: dict) -> int:
    """Get a unique hash for the given registry object."""
    # Seems rather obvious to implement, so I'm doing it before I forget
    # Not sure of usefulness yet
    if registry is _REGISTRY_ADDR2ID:
        # hash by numerical order of ids
        return hash(tuple(sorted(registry.items(), key=lambda x: x[1])))
    if registry is _REGISTRY_ID2REF:
        # hash by memory address (keys)
        return hash(tuple(sorted(registry.keys())))
    if registry is _REGISTRY_WINDOW2WIDGET_COUNT:
        # hash by numerical order of window ids
        return hash(tuple(sorted(registry.items(), key=lambda x: x[0])))
    if registry is _REGISTRY_ID_HIERARCHY:
        raise NotImplementedError("Hierarchy registry hashing not implemented")
    raise ValueError("Unknown registry object")


def _check_instance_type(instance: Any) -> None:
    from src.widget import Widget
    from src.window import Window

    if not isinstance(instance, (Widget, Window)):
        raise TypeError("Instance must be of type Widget or Window")


def _extract_bits(value: int, offset: int, length: int) -> int:
    mask = (1 << length) - 1
    return (value >> offset) & mask


def _get_window_id_from_instance_id(instance_id: int) -> int:
    # Clear the lower N bits to get the Window id
    return instance_id & ~((1 << _BIT_OFFSET) - 1)


def _is_id_a_window_id(instance_id: int) -> bool:
    return _extract_bits(instance_id, 0, _BIT_OFFSET) == 0


def is_instance_registered(instance: object) -> bool:
    """Check if the given instance is registered."""
    _check_instance_type(instance)
    return id(instance) in _REGISTRY_ADDR2ID


def get_registered_instance_id(instance: object) -> int:
    """
    Get the registered unique identifier for the given instance.

    Raises KeyError if the instance is not registered.

    """
    _check_instance_type(instance)
    memory_id = id(instance)
    if memory_id not in _REGISTRY_ADDR2ID:
        raise KeyError("Instance is not registered")
    return _REGISTRY_ADDR2ID[memory_id]


def register_instance_id(instance: object) -> int:
    """
    Get a unique identifier for the given instance.

    Ids are arbitrary sized ints where each 32bits are an individual identifier to an
    object instance. For example, the first 32 bits are the Widget id of a specific
    Window, and the next 32 bits are the Window id of that Widget. This allows for easy
    hierarchical identification of instances, is cheap on storage and allows reference
    access through a simple hashmaps access.

    """
    from src.widget import Widget
    from src.window import Window

    _check_instance_type(instance)

    memory_id = id(instance)
    if memory_id in _REGISTRY_ADDR2ID:
        return _REGISTRY_ADDR2ID[memory_id]

    if isinstance(instance, Window):
        global _WINDOW_ID_COUNTER
        window_id = (1 << _BIT_OFFSET) * _WINDOW_ID_COUNTER
        _WINDOW_ID_COUNTER += 1
        _REGISTRY_ADDR2ID[memory_id] = window_id
        _REGISTRY_WINDOW2WIDGET_COUNT[window_id] = 0
        _REGISTRY_ID2REF[window_id] = instance
        _REGISTRY_ID_HIERARCHY[window_id] = None

    elif isinstance(instance, Widget):
        parent_id = _REGISTRY_ADDR2ID.get(id(instance.parent), None)
        if parent_id is None:
            raise ValueError("Widget instance's parent has no registered id")
        if parent_id not in _REGISTRY_ID_HIERARCHY:
            raise ValueError(
                "Widget instance's parent has no registered hierarchy entry"
            )
        window_id = _get_window_id_from_instance_id(parent_id)
        current_widget_count = _REGISTRY_WINDOW2WIDGET_COUNT.get(window_id, None)
        if current_widget_count is None:
            raise ValueError(
                "Widget instance's parent Window has no registered widget count"
            )
        widget_id = window_id + current_widget_count + 1
        _REGISTRY_WINDOW2WIDGET_COUNT[window_id] += 1
        _REGISTRY_ADDR2ID[memory_id] = widget_id
        _REGISTRY_ID2REF[widget_id] = instance
        hierarchy_entry = _REGISTRY_ID_HIERARCHY[parent_id]
        if hierarchy_entry is None:
            _REGISTRY_ID_HIERARCHY[parent_id] = {widget_id: None}
        else:
            hierarchy_entry[widget_id] = None

    return _REGISTRY_ADDR2ID[memory_id]


class Mixin_WithInstanceIdHierarchy:
    """Mixin class to add hierarchical id management capabilities to widgets and
    alike.
    """

    id: int

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls, *args, **kwargs)
        try:
            self.id = py.read_only_attribute(register_instance_id(self))
        except KeyError as e:
            raise RuntimeError(
                "Failed to register instance id in the internal hierarchy system"
            ) from e
        return self

    def __eq__(self, value):
        return isinstance(value, Mixin_WithInstanceIdHierarchy) and self.id == value.id

    def __ne__(self, value):
        return not self.__eq__(value)

    def __lt__(self, value):
        if not isinstance(value, Mixin_WithInstanceIdHierarchy):
            return NotImplemented
        return self.id < value.id

    def __gt__(self, value):
        if not isinstance(value, Mixin_WithInstanceIdHierarchy):
            return NotImplemented
        return self.id > value.id

    def __le__(self, value):
        if not isinstance(value, Mixin_WithInstanceIdHierarchy):
            return NotImplemented
        return self.id <= value.id

    def __ge__(self, value):
        if not isinstance(value, Mixin_WithInstanceIdHierarchy):
            return NotImplemented
        return self.id >= value.id

    def __contains__(self, item):
        if not isinstance(item, Mixin_WithInstanceIdHierarchy):
            raise TypeError("Impossible for object of this type to be contained")
        if _is_id_a_window_id(self.id):
            # NOTE: Windows cannot contain other Windows
            return False
        for instance_id, _, _ in py.deep_dict_iter_without_recursion(
            _REGISTRY_ID_HIERARCHY
        ):
            if instance_id == item.id:
                return True
        return False

    def __len__(self) -> int:
        tree = None
        if _is_id_a_window_id(self.id):
            tree = _REGISTRY_ID_HIERARCHY.get(self.id, None)
        else:
            for instance_id, subtree, _ in py.deep_dict_iter_without_recursion(
                _REGISTRY_ID_HIERARCHY
            ):
                if instance_id == self.id:
                    tree = subtree
                    break
        if tree is None:
            return 0
        count = 0
        for _, _, is_dict in py.deep_dict_iter_without_recursion(tree):
            if not is_dict:
                count += 1
        return count

    def __iter__(self):
        if _is_id_a_window_id(self.id):
            tree = _REGISTRY_ID_HIERARCHY.get(self.id, None)
        else:
            tree = None
            for instance_id, subtree, _ in py.deep_dict_iter_without_recursion(
                _REGISTRY_ID_HIERARCHY
            ):
                if instance_id == self.id:
                    tree = subtree
                    break
        if tree is None:
            return
        for instance_id, _, is_dict in py.deep_dict_iter_without_recursion(tree):
            if not is_dict:
                yield _REGISTRY_ID2REF[instance_id]

    def __index__(self) -> int:
        return self.id
