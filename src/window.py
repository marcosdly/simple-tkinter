from __future__ import annotations

import src.python_meta as py

from src.state_managers.instance_id import Mixin_WithInstanceIdHierarchy

import tkinter as tk

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from tcltk import TclTk


class Window(Mixin_WithInstanceIdHierarchy):
    toplevel: tk.Toplevel | None
    tcltk: "TclTk"
    is_root: bool

    def __new__(cls, tcltk: "TclTk"):
        self = super().__new__(cls)
        self.tcltk = tcltk
        toplevel = tcltk.tk.winfo_toplevel()
        self.toplevel = toplevel if isinstance(toplevel, tk.Toplevel) else None
        self.is_root = self.toplevel is None
        return self
