from __future__ import annotations

from typing import Any


__all__ = [
    "is_instance_registered",
    "get_registered_instance_id",
    "register_instance_id",
]


_REGISTRY: dict[int, int] = {}
"""Registry mapping instance memory ids to unique object references."""

_WINDOW_ID_COUNTER: int = 0
"""
Counter for assigning unique Window ids.

Not to be in any way related to: the number of Windows registered, the order of
registration, it's position in the children hierarchy.

"""

_BIT_OFFSET = 32


def _check_instance_type(instance: Any) -> None:
    from src.widget import Widget
    from src.window import Window

    if not isinstance(instance, (Widget, Window)):
        raise TypeError("Instance must be of type Widget or Window")


def is_instance_registered(instance: object) -> bool:
    """Check if the given instance is registered."""
    _check_instance_type(instance)
    return id(instance) in _REGISTRY


def get_registered_instance_id(instance: object) -> int:
    """
    Get the registered unique identifier for the given instance.

    Raises KeyError if the instance is not registered.

    """
    _check_instance_type(instance)
    memory_id = id(instance)
    if memory_id not in _REGISTRY:
        raise KeyError("Instance is not registered")
    return _REGISTRY[memory_id]


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
    if memory_id in _REGISTRY:
        return _REGISTRY[memory_id]

    if isinstance(instance, Window):
        global _WINDOW_ID_COUNTER
        _WINDOW_ID_COUNTER += 1
        _REGISTRY[memory_id] = _WINDOW_ID_COUNTER << _BIT_OFFSET

    if isinstance(instance, Widget):
        parent_id = _REGISTRY.get(id(instance.parent), None)
        if parent_id is None:
            raise ValueError("Widget instance's parent has no registered id")
        _REGISTRY[memory_id] = parent_id + 1

    return _REGISTRY[memory_id]
