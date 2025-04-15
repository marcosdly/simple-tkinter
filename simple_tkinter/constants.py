from __future__ import annotations

from typing import Literal


W = LEFT = "w"
E = RIGHT = "e"
N = TOP = "n"
S = BOTTOM = "s"
NSEW = ALL_DIRECTIONS = N + S + E + W
Direction = Literal[
    LEFT,
    RIGHT,
    TOP,
    BOTTOM,
    LEFT + RIGHT,
    TOP + BOTTOM,
    TOP + LEFT,
    TOP + RIGHT,
    BOTTOM + LEFT,
    BOTTOM + RIGHT,
]
