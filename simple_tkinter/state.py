from __future__ import annotations

from typing import Any, Callable, Hashable
from uuid import UUID


StateEventCallable = Callable[[], Any]
EventStateByValue = dict[Hashable, StateEventCallable]
StateMapping = dict[str, Hashable]

class State(StateMapping):
    parent_id: UUID
    call_when: dict[str, EventStateByValue]
    call_if: dict[StateMapping, StateEventCallable]

    def __init__(self, parent_instance_id: UUID):
        super().__init__()
        self.parent_id = parent_instance_id
        self.call_when = {}
        self.call_if = {}

    def __setitem__(self, name: str, value: Hashable):
        super()[name] = value
        _event_map = self.call_when.get(name, None)
        # run event defined by value
        if _event_map is None:
            self.call_when[name] = {}
            return
        try:
            _event_map[value]()
        except (KeyError, TypeError):
            pass
        # run events defined by value mapping (condition)
        for cond_map, action_callable in self.call_if.items():
            if name not in cond_map:
                continue
            if all(self[key] == value for key, value in cond_map.items() if key in self):
                action_callable()

    def __delitem__(self, name: str):
        try:
            super().__delitem__(name)
        except KeyError:
            return

