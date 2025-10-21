from __future__ import annotations

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

_REGISTRY_ID_HIERARCHY: IdHierarchy = {}  # TODO Implement
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


def _get_window_id_from_instance_id(instance_id: int) -> int:
    # Clear the lower N bits to get the Window id
    return instance_id & ~((1 << _BIT_OFFSET) - 1)


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

    elif isinstance(instance, Widget):
        parent_id = _REGISTRY_ADDR2ID.get(id(instance.parent), None)
        if parent_id is None:
            raise ValueError("Widget instance's parent has no registered id")
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

    return _REGISTRY_ADDR2ID[memory_id]
