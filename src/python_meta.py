from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Generic, TypeVar, cast

_T = TypeVar("_T")
_V = TypeVar("_V")


class MetaProgrammingError(Exception):
    """Exception raised for errors in meta-programming constructs."""

    _prefix: str = "Error in internal meta-programming construct: "

    def __init__(self, *args):
        super().__init__(self._prefix, *args)


class read_only_attribute(Generic[_V]):
    """Class attribute that is read-only after initialization."""

    if TYPE_CHECKING:

        def __new__(
            cls, value: _V | None = None, *, assign_later: bool = False
        ) -> _V: ...

    def __init__(self, value: _V | None = None, *, assign_later: bool = False):
        self._value: _V | None = value
        self._assigned = not assign_later

    def __set_name__(self, owner, name: str) -> None:
        self.owner = owner
        self.name = name

    def __get__(self, instance, owner) -> _V:
        return cast(_V, self._value)

    def __set__(self, instance, value: _V):
        if not self._assigned:
            self._value = value
            self._assigned = True
            return
        raise AttributeError("This property is read-only") from MetaProgrammingError(
            f"Attempted to re-assign read-only attribute '{self.name}' of class '{self.owner.__name__}'"
        )


class single_eval_cached_property(Generic[_T, _V]):
    """Class attribute that wraps a function to be evaluated only once upon first access.
    The consumer is only exposed to the returned value."""

    if TYPE_CHECKING:

        def __new__(cls, func: Callable[[_T], _V]) -> _V: ...

    def __init__(self, func: Callable[[_T], _V]):
        try:
            self._evaluated = False
            self.func: Callable[[_T], _V] = func
            self._value: _V
        except Exception as e:
            raise e from MetaProgrammingError(f"Failed to initialize {self.__class__}")

    def __get__(self, instance, owner) -> _V:
        if not self._evaluated:
            try:
                self._value = self.func.__get__(instance, owner)()
            except Exception as e:
                raise e from MetaProgrammingError(
                    f"Failed to evaluate cached property '{self.name}' of class '{self.owner}'"
                )
            self._evaluated = True
        return self._value

    def __set_name__(self, owner, name: str) -> None:
        self.owner = owner
        self.name = name

    def __set__(self, instance, value):
        raise AttributeError("This property is read-only") from MetaProgrammingError(
            f"Attempted to re-assign read-only property '{self.name}' of class '{self.owner.__name__}'"
        )
