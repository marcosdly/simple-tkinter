from __future__ import annotations

from simple_tkinter.constants import Direction

import io
import os
import copy
import json
import math
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

_tk_inited: bool = False


def _ensure_tk():
    global _tk_inited
    if not _tk_inited:
        _ = tk.Tcl(useTk=True)
        _tk_inited = True


# region Common types

T = TypeVar("T")
ElementType = Literal["outline", "label", "frame", "grid", "flexbox"]
ElementPropertyType = Literal[
    "border", "text", "background", "position", "size", "grid", "flexbox"
]
OrderedSequence = Union[list[T], tuple[T, ...]]
Image = Union[str, Path, bytes, bytearray, io.BytesIO]
PropertyType = Union[
    str,
    int,
    float,
    bool,
    Image,
    "Color",
    "Size",
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

# region Size

Size = Union["SizeAbsolute", "SizeRelative"]


@final
class SizeAbsolute(NamedTuple):
    value: float = 0
    unit: Literal["px", "pt", "cm", "in", "mm"] = "px"


@final
class SizeRelative(NamedTuple):
    value: float = 0
    unit: Literal["percent", "part"] = "percent"
    relative_to: Literal["widget", "id", "class"] = "widget"
    identifier: str = "parent"


# endregion Size

# region Color


class Color(str):
    # SEE formulas sources: https://exceloffthegrid.com/convert-color-codes/
    def __new__(cls, hex_value: str) -> Color:
        hex_value = hex_value.strip("#")
        _len = len(hex_value)
        if _len == 0:
            raise ValueError("hex string length is zero")
        for char in hex_value:
            if char not in "0123456789abcdef":
                raise ValueError(f"invalid hex character: '{char}' in {hex_value}")
        value: str
        if _len == 1:
            value = hex_value * 6
        elif _len == 2:
            value = hex_value * 3
        elif _len == 3:
            value = hex_value * 2
        elif _len == 6:
            value = hex_value
        else:
            raise ValueError(f"hex string length must be up to 6 but got {_len}")
        return super(Color, cls).__new__(cls, "#" + value)

    @classmethod
    def rgb(cls, r: int, g: int, b: int) -> Color:
        def clamp(n: int) -> int:
            return min(max(n, 0), 255)

        return cls.int(clamp(b) * 256**2 + clamp(g) * 256 + clamp(r))

    @classmethod
    def hsl(cls, hue: int, sat: float, lum: float) -> Color:
        if sat == 0:
            gray_shade: int = max(math.floor(lum * 255), 255)
            return cls.rgb(gray_shade, gray_shade, gray_shade)

        temp1: float
        if lum < 0.5:
            temp1 = lum * (sat + 1)
        else:
            temp1 = lum + sat - lum * sat
        temp2: float = 2 * lum - temp1
        hue_adjusted: float = hue / 360

        def color_temperature(temp: float) -> float:
            if temp < 0:
                return temp + 1
            elif temp > 1:
                return temp - 1
            else:
                return temp

        temp_r = color_temperature(hue_adjusted + 0.333)
        temp_g = color_temperature(hue_adjusted)
        temp_b = color_temperature(hue_adjusted - 0.333)

        def rgb_factor(temp: float) -> float:
            if temp * 6 < 1:
                return temp2 + (temp1 - temp2) * 6 * temp
            elif temp * 2 < 1:
                return temp1
            elif temp * 3 < 2:
                return temp2 + (temp1 - temp2) * (0.666 - temp) * 6
            else:
                return temp2

        def rgb_value(temp: float) -> int:
            return math.floor(rgb_factor(temp) * 255)

        return cls.rgb(rgb_value(temp_r), rgb_value(temp_g), rgb_value(temp_b))

    @classmethod
    def int(cls, n: int) -> Color:
        return Color(hex(n)[2:].ljust(6, "0"))

    @classmethod
    def hsv(cls, hue: float, sat: float, val: float) -> Color:
        c: float = sat * val
        x: float = c * (1 - abs(hue / 60 - 2 * math.floor(hue / 60 / 2) - 1))
        m: float = val - c

        def rgb_value(n: float) -> int:
            return math.floor((math.floor(n) + m) * 255)

        if 0 <= hue < 60:
            return cls.rgb(rgb_value(c), rgb_value(x), 0)
        elif 60 <= hue < 120:
            return cls.rgb(rgb_value(x), rgb_value(c), 0)
        elif 120 <= hue < 180:
            return cls.rgb(0, rgb_value(c), rgb_value(x))
        elif 180 <= hue < 240:
            return cls.rgb(0, rgb_value(x), rgb_value(c))
        elif 240 <= hue < 300:
            return cls.rgb(rgb_value(x), 0, rgb_value(c))
        else:
            return cls.rgb(rgb_value(c), 0, rgb_value(x))

    @classmethod
    def cmyk(cls, c: float, m: float, y: float, k: float) -> Color:
        return cls.rgb(
            math.floor(255 * (1 - k) * (1 - c)),
            math.floor(255 * (1 - k) * (1 - m)),
            math.floor(255 * (1 - k) * (1 - y)),
        )


# endregion Color

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
