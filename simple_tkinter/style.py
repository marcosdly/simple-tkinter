from __future__ import annotations

from simple_tkinter.constants import Direction

import io
import os
import copy
import json
import uuid
import numbers
import tkinter as tk
import itertools
import contextvars
import tkinter.font as tk_font

from typing import (
    Any,
    Final,
    Union,
    Generic,
    Literal,
    TypeVar,
    Callable,
    Optional,
    TypedDict,
    NamedTuple,
    cast,
    final,
    overload,
)
from pathlib import Path
from contextvars import Context, ContextVar
from dataclasses import field, asdict, dataclass
from collections.abc import Mapping


VSAPI_IMPL_THEMES: tuple[str, ...] = (
    ("winnative", "vista", "xpnative") if os.name == "nt" else ()
)

# region Common types

T = TypeVar("T")
ElementType = Literal["outline", "label", "frame", "grid", "flexbox"]
ElementPropertyType = Literal[
    "border", "text", "background", "position", "size", "grid", "flexbox"
]
OrderedSequence = Union[list[T], tuple[T, ...]]
Image = Union[str, Path, bytes, bytearray, io.BytesIO]
Color = str
Size = float
PropertyType = Union[
    str,
    int,
    float,
    bool,
    Image,
    Color,
    Size,
    "Spacing[int]",
    "Font",
    None,
    Callable[..., Any],
    Final[str],
    dict[str, "PropertyType"],
]

# endregion Common types

# region Font type and helpers


class Font(TypedDict, total=False):
    family: str
    size: Size
    italic: bool
    bold: bool
    underline: bool
    strikethrough: bool

    @classmethod
    def get_standard_font(
        cls, alias: Literal["sans", "serif", "monospace"]
    ) -> Font: ...  # type: ignore[reportGeneralTypeIssues]

    @classmethod
    def get_families(cls) -> tuple[str, ...]: ...  # type: ignore[reportGeneralTypeIssues]

    @classmethod
    def get_sub_families(cls) -> dict[str, tuple[str, ...]]: ...  # type: ignore[reportGeneralTypeIssues]

    @classmethod
    def get_files(cls) -> dict[str, Path]: ...  # type: ignore[reportGeneralTypeIssues]

    @classmethod
    def get_by_name(cls, font_name: str) -> Font: ...  # type: ignore[reportGeneralTypeIssues]

    @classmethod
    def create_font_as_config_alias(cls, new_alias: str, font_config: Font): ...  # type: ignore[reportGeneralTypeIssues]


# endregion Font: type and helpers

# region Spacing

NT = TypeVar("NT", int, float)


@final
class Spacing(Generic[NT], NamedTuple):
    __ZERO = cast(NT, 0)

    left: NT = __ZERO
    right: NT = __ZERO
    top: NT = __ZERO
    bottom: NT = __ZERO

    @classmethod
    def equal_horizontal(cls, size: NT):
        return cls(left=size, right=size)

    @classmethod
    def equal_vertical(cls, size: NT):
        return cls(top=size, bottom=size)

    @classmethod
    def equal_around(cls, size: NT):
        return cls(size, size, size, size)


# endregion Spacing


# region TYPES: Style properties


class StyleBorder(TypedDict, total=False):
    color: Color
    width: Size


class StyleText(TypedDict, total=False):
    placeholder: Union[str, None]
    placeholder_as_content: bool
    content: Union[str, None]
    font: Font
    foreground: Color
    underline: bool
    justify: Literal["left", "right", "center", "justify"]
    wrap: bool
    wrap_length: int
    wrap_break_at: Union[str, Callable[[str, int], int]]


class StyleBackground(TypedDict, total=False):
    color: Color
    image: Image


class StylePosition(TypedDict, total=False):
    absolute: bool
    origin: Direction
    x: Size
    y: Size
    z: int


class StyleSize(TypedDict, total=False):
    w: Size
    h: Size


class StyleSpacing(TypedDict, total=False):
    padding: Spacing[int]
    margin: Spacing[int]


class StyleFlexbox(TypedDict, total=False): ...


class StyleGrid(TypedDict, total=False): ...


# endregion TYPES: Style properties


# region TYPES: Primitive elements' style properties


class OutlineElementProperties(TypedDict, total=False):
    border: StyleBorder
    spacing: StyleSpacing


class LabelElementProperties(TypedDict, total=False):
    text: StyleText
    spacing: StyleSpacing
    position: StylePosition
    size: StyleSize


class FrameElementProperties(TypedDict, total=False):
    spacing: StyleSpacing
    position: StylePosition
    size: StyleSize
    background: StyleBackground


class FlexboxElementProperties(TypedDict, total=False):
    spacing: StyleSpacing
    position: StylePosition
    size: StyleSize
    flexbox: StyleFlexbox


class GridElementProperties(TypedDict, total=False):
    spacing: StyleSpacing
    position: StylePosition
    size: StyleSize
    grid: StyleGrid


ElementTypeStyle = Union[
    OutlineElementProperties,
    LabelElementProperties,
    FrameElementProperties,
    FlexboxElementProperties,
    GridElementProperties,
]

# endregion TYPES: Primitive elements' style properties


# region TYPES: Primitive elements' implementations


class ElementStyleDefinition(TypedDict, total=True):
    element_type: ElementType
    style_id: Union[str, None]
    style_class: Union[str, None]
    style_defaults: ElementTypeStyle
    style_can_edit: dict[ElementPropertyType, Union[bool, dict[str, bool]]]
    children: StyleDefinition


# endregion TYPES: Primitive elements' implementations

# region Style object (mapping) implementation

StyleDefinition = OrderedSequence[ElementStyleDefinition]

StyleObjectValue = Union[PropertyType, "Style"]


@dataclass(frozen=True, unsafe_hash=True)
class StyleObjectContext:
    keytrace: ContextVar[tuple[str, ...]]
    instance_chain_hash: int
    context: Context

    @classmethod
    def make_default(cls):
        ctx = Context()

        def populate_context(*, running_context: Context):
            return cls(
                keytrace=ContextVar("keytrace", default=()),
                instance_chain_hash=uuid.uuid4().int,
                context=running_context,
            )

        return ctx.run(populate_context, running_context=ctx)


StyleObjectEventCallback = Callable[[str, PropertyType, PropertyType], Any]


@final
class Style(Mapping[str, StyleObjectValue]):
    def __init__(
        self,
        mapping: dict[str, PropertyType],
        *,
        context: Optional[StyleObjectContext] = None,
        on_get_value: Optional[Callable[[str, StyleObjectValue], Any]] = None,
        on_set_value: Optional[
            Callable[[str, StyleObjectValue, StyleObjectValue], Any]
        ] = None,
    ):
        self._on_get_value = on_get_value
        self._on_set_value = on_set_value
        self._ctx: StyleObjectContext = context or StyleObjectContext.make_default()

        self._data: dict[str, StyleObjectValue] = {}
        tmp_slots: list[str] = []
        for k, v in mapping.items():
            value: Union[StyleObjectValue, "Style"] = (
                Style(
                    cast(dict[str, PropertyType], v),
                    context=self._ctx,
                    on_get_value=self._on_get_value,
                    on_set_value=self._on_set_value,
                )
                if isinstance(v, dict)
                else v
            )
            self._data[k] = value
            tmp_slots.append(k)

        self.slots: tuple[str, ...] = tuple(tmp_slots)

    def __getitem__(self, name: str):
        if name not in self.slots:
            raise KeyError(name)
        value = self._data.__getitem__(name)
        if isinstance(value, (dict, Style)):
            updated_trace = self._ctx.keytrace.get() + (name,)
            _ = self._ctx.keytrace.set(updated_trace)
        else:
            if self._on_get_value is not None:
                self._ctx.context.run(self._on_get_value, name, value)
            _ = self._ctx.keytrace.set(())
        return value

    def __setitem__(self, name: str, value: PropertyType):
        if name not in self.slots:
            raise KeyError(f"unknown key {name}")
        previous_value = self._data.get(name, None)
        if isinstance(previous_value, (dict, Style)):
            raise TypeError("trying to assign key with value of type 'dict' or 'Style'")
        self._data.__setitem__(name, value)
        if self._on_set_value is not None:
            self._ctx.context.run(self._on_set_value, name, previous_value, value)

    def __iter__(self):
        return self._data.__iter__()

    def __len__(self):
        return self._data.__len__()

    def __contains__(self, name: str):
        return self._data.__contains__(name)

    def __eq__(self, other: Any):
        return self._data.__eq__(other)

    def __ne__(self, other: Any):
        return self._data.__eq__(other)

    def keys(self):
        return self._data.keys()

    def items(self):
        return self._data.items()

    def values(self):
        return self._data.values()

    def get(self, name: str, default: Optional[StyleObjectValue] = None):
        return self._data.get(name, default)

    def update(
        self, mapping: dict[str, StyleObjectValue], /, **kwargs: StyleObjectValue
    ):
        changed: set[str] = set()
        # prefer kwargs
        for k, v in itertools.chain(kwargs.items(), mapping.items()):
            if k in changed:
                continue
            value = copy.deepcopy(v) if isinstance(v, (dict, Style)) else v
            changed.add(k)
            self.__setitem__(k, cast(dict[str, PropertyType], value))

    def __deepcopy__(self):
        return cast(dict[str, PropertyType], copy.deepcopy(self._data))

    def __copy__(self):
        return self.__deepcopy__()

    def deepcopy(self):
        return self.__deepcopy__()

    def get_style_chain_hash(self) -> int:
        return self._ctx.instance_chain_hash


# endregion Style object (mapping) implementation


def style_factory(): ...
