from __future__ import annotations

from simple_tkinter.constants import Direction

import os
import io
from pathlib import Path

from typing import Union, Literal, TypeVar, Callable, TypedDict, NamedTuple


VSAPI_IMPL_THEMES: tuple[str, ...] = (
    ("winnative", "vista", "xpnative") if os.name == "nt" else ()
)

Image = Union[str, Path, bytes, bytearray, io.BytesIO]
Color = str
Size = float

class Font(TypedDict, total=False):
    family: str
    size: Size
    italic: bool
    bold: bool
    underline: bool
    strikethrough: bool

class Spacing(NamedTuple):
    left: float = 0
    right: float = 0
    top: float = 0
    bottom: float = 0


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
    justify: Literal['left', 'right', 'center', 'justify']
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
    padding: Spacing
    margin: Spacing


class StyleFlexbox(TypedDict, total=False): ...


class StyleGrid(TypedDict, total=False): ...


T = TypeVar("T")

ElementType = Literal["outline", "label", "frame", "grid", "flexbox"]
ElementPropertyType = Literal[
    "border", "text", "background", "position", "size", "grid", "flexbox"
]
OrderedSequence = Union[list[T], tuple[T, ...]]


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


class ElementStyleDefinition(TypedDict, total=True):
    element_type: ElementType
    style_id: Union[str, None]
    style_class: Union[str, None]
    style_defaults: ElementTypeStyle
    style_can_edit: dict[ElementPropertyType, Union[bool, dict[str, bool]]]
    children: StyleDefinition


StyleDefinition = OrderedSequence[ElementStyleDefinition]


def style_factory(): ...

