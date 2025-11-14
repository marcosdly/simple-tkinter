from __future__ import annotations

import src.python_meta as py

import tkinter as tk

from typing import TYPE_CHECKING, Any, Union, Callable, Iterable, Generator, TypedDict
from tkinter import ttk
from contextlib import contextmanager


WidgetLike = Union[tk.Widget, ttk.Widget, tk.Toplevel, tk.Tk]


class StyleAnnotation(TypedDict):
    name: str
    type: type[StyleValueType]
    apply: StyleApplyFunc
    default: StyleValueType | StyleValueFactory


class _StyleDefinitionState(TypedDict, total=False):
    defined: bool
    is_defining: bool
    widget: WidgetLike


StyleApplyFunc = Union[
    Callable[[Union[tk.Widget, ttk.Widget], "StyleValueType", "StyleValueType"], None],
    Callable[[Union[tk.Widget, ttk.Widget], "StyleValueType"], None],
    Callable[[Union[tk.Widget, ttk.Widget]], None],
]

StyleValueFactory = Callable[[], "StyleValueType"]

StyleValueType = Union[int, float, str, bool, tuple[Any], list[Any], dict[str, Any]]


class StyleApplyError(RuntimeError):
    """
    Exception raised when a style apply function fails.

    Style apply functions are internal in the sense they are (or should be) declared at
    class instanciation or init.

    It is a RuntimeError due to it being considered core behavior. For a less formal way
    of reacting to style changes, consider using event bindings.

    Multiple error checks may occur in the contexts this exception is raised and the
    property `errors` contains them all for debugging purposes.

    There is no 'master' or 'root' error, as this exception represents a context, like
    an explicit wrapper/flag for the context of applying styles.

    """

    name: str
    errors: tuple[Exception, ...]

    def __init__(self, *, name: str, error_chain: Iterable[Exception] = ()) -> None:
        super().__init__(f"Style apply function '{name}'")
        self.name = name
        self.errors = tuple(error_chain)


def hash_style_value(v: StyleValueType | StyleValueFactory) -> int:
    if isinstance(v, (int, float, str, bool)):
        return hash(v)
    elif isinstance(v, (list, tuple)):
        h = 0
        for item in v:
            h ^= hash_style_value(item)
        return h
    elif isinstance(v, dict):
        h = 0
        for key, value in v.items():
            h ^= hash(key) ^ hash_style_value(value)
        return h
    elif callable(v):
        return id(v)
    else:
        raise TypeError(f"Unhashable style value type: {type(v)}")


StyleDefDecorator = Callable[
    [str, type[StyleValueType], Union[StyleValueType, StyleValueFactory]],
    Callable[[StyleApplyFunc], StyleApplyFunc],
]


class Mixin_WithStyle:
    """
    Standalone mixin class to add style management capabilities to widgets and widget-
    like.

    Usage:

    .. code:: python
        class MyWidget(Mixin_WithStyle):
            style: Mixin_WithStyle

            def _define_style_properties(
                self, define_style: StyleDefDecorator,
            ) -> None:
                @define_style("bg_color", str, default="white")
                def apply_bg_color(widget, value, previous_value, /) -> None:
                    widget.config(bg=value)

        >>> my_widget = MyWidget(some_tk_widget)
        >>> my_widget["bg_color"] = "#AABBCC"

    Amount of parameters in the apply function may vary (1 to 3), depending on what
    information is needed.

    The order of parameters is always: `widget`, `value`, `previous_value`. For example:

    .. code:: python
        @define_style("some_stateless_style", int, default=0)
        def apply(widget, /) -> None:
            ...

        @define_style("some_stateful_simple_style", int, default=0)
        def apply(widget, value, /) -> None:
            ...

        @define_style("some_stateful_complex_style", int, default=0)
        def apply(widget, value, previous_value, /) -> None:
            ...

    Styles cannot be re-defined once the class has been created, thus why the
    `_define_style_properties` abstract method exists - apart from allowing the class
    to be self contained.

    """

    style: Mixin_WithStyle

    __style_annotations: dict[str, StyleAnnotation]
    __style_def_state: _StyleDefinitionState
    __style_state: dict[str, StyleValueType | StyleValueFactory]
    __style_hash: dict[str, int]

    def __new__(
        cls,
        /,
        *args,
        style_target_widget: WidgetLike,
        **kwargs,
    ) -> Mixin_WithStyle:
        self = super().__new__(cls, *args, **kwargs)
        self.__style_annotations = {}
        self.__style_state = {}
        self.__style_hash = {}
        self.__style_def_state = {}

        with self.__make_style_annotations_context(
            style_target_widget
        ) as new_style_annotation_decorator:
            self._define_style_properties(new_style_annotation_decorator)

        return self

    def __get_style_state(
        self,
        key: str,
        *,
        allow_foreign_side_effects: bool = False,
        allow_self_side_effects: bool = False,
    ) -> StyleValueType:
        """
        Get the style state value for the given key and handle cases like factories,
        hashing, caching, forcing particular behavior, etc if (and only if) side effects
        are allowed.

        NOTE: This function is verbose to signal that simply getting style values may
        directly cause third-party side effects.

        Foreign side effects are unpredictable and disabled by default even though they
        may be the only way to get the value.

        Internal side effects are those that affect only this instance and are safe to
        allow, but are still disabled by default to avoid unexpected behavior and trust
        issues.

        NOTE: Allowing foreign while disallowing self side effects will cause foreign
        side effects for each such call.

        """
        value = self.__style_state[key]
        if callable(value):
            if not allow_foreign_side_effects:
                err = RuntimeError(
                    f"Getting style value for key '{key}' requires side effects to be allowed because an arbitrary factory callable must be called"
                )
                raise StyleApplyError(name=key, error_chain=[err])
            value = value()
        if allow_self_side_effects:
            self.__style_state[key] = value
            self.__style_hash[key] = hash_style_value(value)
        return value

    def __set_style_state(
        self, key: str, value: StyleValueType | None = None, *, reset: bool = False
    ) -> StyleValueType:
        """Set the style state value for the given key and handle cases like hashing,
        caching, forcing particular behavior, etc.
        """
        style_annotation = self.__style_annotations[key]

        if reset:
            if value is not None:
                raise ValueError(
                    f"Cannot provide value when resetting style, got {value}"
                )

            value = self.__get_style_state(
                key, allow_foreign_side_effects=True, allow_self_side_effects=True
            )
        else:
            if value is None:
                raise ValueError(
                    f"Style value for key '{key}' cannot be None unless resetting"
                )

        _type = style_annotation["type"]
        if not isinstance(value, _type):
            raise TypeError(
                f"Style value for key '{key}' must be of type {_type}, got {type(value)}"
            )

        prev = self.__get_style_state(
            key, allow_foreign_side_effects=True, allow_self_side_effects=True
        )
        curr = self.__style_state[key] = value
        apply = style_annotation["apply"]
        widget = self.__style_def_state.get("widget")
        if TYPE_CHECKING:
            assert isinstance(widget, (tk.Widget, ttk.Widget))

        # try 3 args
        ok, err = py.pcall(apply, widget, curr, prev)
        if ok:
            return self.__get_style_state(
                key, allow_foreign_side_effects=True, allow_self_side_effects=True
            )
        error_chain = []
        error_chain.append(err)

        # try 2 args
        ok, err = py.pcall(apply, widget, curr)
        if ok:
            return self.__get_style_state(
                key, allow_foreign_side_effects=True, allow_self_side_effects=True
            )
        error_chain.append(err)

        # try 1 args
        ok, err = py.pcall(apply, widget)
        if ok:
            return self.__get_style_state(
                key, allow_foreign_side_effects=True, allow_self_side_effects=True
            )
        error_chain.append(err)

        raise StyleApplyError(name=key, error_chain=error_chain)

    def _define_style_properties(
        self,
        define_style: StyleDefDecorator,
    ) -> None: ...

    @contextmanager
    def __make_style_annotations_context(
        self, widget: WidgetLike
    ) -> Generator[StyleDefDecorator, None, None]:
        if self.__style_def_state.get("is_defining", False):
            raise RuntimeError(
                "Style declaration context for this class is already active"
            )
        self.__style_def_state["is_defining"] = True
        _defined_err = RuntimeError("Styles have already been defined for this class")
        if self.__style_def_state.get("defined", False):
            raise _defined_err
        self.__style_def_state["defined"] = False
        self.__style_def_state["widget"] = widget

        def decorator(
            name: str,
            type_: type[StyleValueType],
            default: StyleValueType | StyleValueFactory,
        ) -> Callable[[StyleApplyFunc], StyleApplyFunc]:
            if self.__style_def_state.get("defined", False):
                raise _defined_err

            def setup_style_state(func: StyleApplyFunc) -> StyleApplyFunc:
                if self.__style_def_state.get("defined", False):
                    raise _defined_err
                annotation = StyleAnnotation(
                    name=name,
                    type=type_,
                    apply=func,
                    default=default,
                )
                if name in self.__style_annotations:
                    raise ValueError(f"Style annotation '{name}' is already defined")
                self.__style_annotations[name] = annotation
                self.__style_state[name] = default
                self.__style_state.setdefault(name, default)
                self.__style_hash[name] = hash_style_value(default)
                self.__set_style_state(name, None, reset=True)
                return func

            return setup_style_state

        yield decorator

        self.__style_def_state["is_defining"] = False
        self.__style_def_state["defined"] = True

    def _get_style_hash(self) -> int:
        """Compute and return the hash of the current style state."""
        h = 0
        for key, precomputed_hash in self.__style_hash.items():
            h ^= hash(key) ^ precomputed_hash
        return h

    def __getitem__(self, key: str, /) -> StyleValueType:
        """
        Gets the style state value for the given key and handle side effects.

        If the style key (name) doesn't exist, try calling the superclass __getitem__
        instead. On failure, raise the original error from setting the style state.

        """
        if key in self.__style_state:
            return self.__get_style_state(
                key, allow_foreign_side_effects=False, allow_self_side_effects=False
            )
        try:
            return super().__getitem__(key)  # type: ignore
        except AttributeError:
            raise KeyError(f"Style key '{key}' not found")

    def __setitem__(self, key: str, value: StyleValueType, /) -> None:
        """
        Sets the style state value for the given key and handle side effects.

        If the style key (name) doesn't exist, try calling the superclass __setitem__
        instead. On failure, raise the original error from setting the style state.

        """
        if key not in self.__style_annotations:
            # is not style, handle as normal item setting
            try:
                super().__setitem__(key, value)  # type: ignore
                return
            except (AttributeError, KeyError):
                # __setitem__ not defined in superclass or key not found, so assume
                # the consumer wanted to access a style key
                raise KeyError(f"Style key '{key}' not found")
        ok, err = py.pcall(self.__set_style_state, key, value)
        if ok:
            return
        if TYPE_CHECKING:
            assert isinstance(err, Exception)
        raise err


def test_style_mixin(tk_root, tk_tick):
    toplevel = tk_root.winfo_toplevel()
    before = "lorem ipsum"
    after = "dolor sit amet"

    class TestWidget(Mixin_WithStyle):
        def _define_style_properties(self, define_style: StyleDefDecorator) -> None:
            @define_style("title", str, default=before)
            def apply_title(widget, value, /) -> None:
                if isinstance(widget, tk.Toplevel):
                    widget.title(value)
                else:
                    widget.wm_title(value)

    test_widget = TestWidget(style_target_widget=toplevel)
    tk_tick()
    assert test_widget["title"] == before, "pre-action: custom getter failed"
    assert toplevel.title() == before, "pre-action: wrapped widget state unchanged"
    test_widget["title"] = after
    tk_tick()
    assert test_widget["title"] == after, "post-action: custom getter failed"
    assert toplevel.title() == after, "post-action: wrapped widget state unchanged"
