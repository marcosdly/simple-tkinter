from __future__ import annotations

import tkinter as tk

from typing import TYPE_CHECKING, Any, Union, Callable, Generator, TypedDict
from tkinter import ttk
from contextlib import contextmanager


WidgetLike = Union[tk.Widget, ttk.Widget, tk.Toplevel, tk.Tk]


class StyleAnnotation(TypedDict):
    name: str
    type: type[StyleValueType]
    apply: StyleApplyFunc
    default: StyleValueType | StyleValueFactory


class StyleDefinitionState(TypedDict, total=False):
    defined: bool
    is_defining: bool
    widget: WidgetLike


StyleApplyFunc = Callable[
    [Union[tk.Widget, ttk.Widget], "StyleValueType", "StyleValueType"], None
]

StyleValueFactory = Callable[[], "StyleValueType"]

StyleValueType = Union[int, float, str, bool, tuple[Any], list[Any], dict[str, Any]]


class StyleApplyError(RuntimeError):
    def __init__(self, *, name: str) -> None:
        super().__init__(f"Style apply function '{name}'")


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


StyleAnnotations = dict[str, StyleAnnotation]

StyleState = dict[str, Union[StyleValueType, StyleValueFactory]]

StyleHashCache = dict[str, int]

StyleDefDecorator = Callable[
    [str, type[StyleValueType], Union[StyleValueType, StyleValueFactory]],
    Callable[[StyleApplyFunc], StyleApplyFunc],
]


class StyleMapping:
    __style_annotations: StyleAnnotations
    __style_state: StyleState
    __style_hash: StyleHashCache
    __style_def_state: StyleDefinitionState

    def __init__(self, widget: WidgetLike, define_callback) -> None:
        self.__style_annotations = {}
        self.__style_state = {}
        self.__style_hash = {}
        self.__style_def_state = {}
        with self.__make_style_annotations_context(
            widget
        ) as new_style_annotation_decorator:
            define_callback(new_style_annotation_decorator)

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
                raise StyleApplyError(name=key) from err
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

        try:
            apply(widget, curr, prev)
            return self.__get_style_state(
                key, allow_foreign_side_effects=True, allow_self_side_effects=True
            )
        except Exception as e:
            raise StyleApplyError(name=key) from e

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
        self.__set_style_state(key, value)


class Mixin_WithStyle:
    """
    Standalone mixin class to add style management capabilities to widgets and widget-
    like.

    Usage:

    .. code:: python
        class MyWidget(Mixin_WithStyle):
            def _define_style_properties(
                self, define_style: StyleDefDecorator,
            ) -> None:
                @define_style("bg_color", str, default="white")
                def apply_bg_color(widget, value, previous_value, /) -> None:
                    widget.config(bg=value)

        >>> my_widget = MyWidget(some_tk_widget)
        >>> my_widget["bg_color"]
        'white'
        >>> my_widget["bg_color"] = "#AABBCC"
        >>> my_widget["bg_color"]
        '#AABBCC'

    Styles cannot be re-defined once the class has been instantiated, thus why the
    `_define_style_properties` abstract method exists - apart from allowing the class
    to be self contained.

    """

    style: StyleMapping

    def _define_style_properties(
        self,
        define_style: StyleDefDecorator,
    ) -> None: ...

    def __init__(
        self,
        *,
        style_target_widget: WidgetLike,
    ) -> None:
        self.style = StyleMapping(style_target_widget, self._define_style_properties)


def test_style_mixin(tk_root, tk_tick):
    toplevel = tk_root.winfo_toplevel()
    before = "lorem ipsum"
    after = "dolor sit amet"

    class TestWidget(Mixin_WithStyle):
        def _define_style_properties(self, define_style: StyleDefDecorator) -> None:
            @define_style("title", str, default=before)
            def apply_title(widget, value, _) -> None:
                if isinstance(widget, tk.Toplevel):
                    widget.title(value)
                else:
                    widget.wm_title(value)

    test_widget = TestWidget(style_target_widget=toplevel)
    tk_tick()
    assert test_widget.style["title"] == before, "pre-action: custom getter failed"
    assert toplevel.title() == before, "pre-action: wrapped widget state unchanged"
    test_widget.style["title"] = after
    tk_tick()
    assert test_widget.style["title"] == after, "post-action: custom getter failed"
    assert toplevel.title() == after, "post-action: wrapped widget state unchanged"
