from __future__ import annotations

import src.python_meta as py
import src.state_managers as state_managers

import tkinter as tk

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from tcltk import TclTk


class Window:
    tcltk: "TclTk"
    is_root: bool
    _toplevel: tk.Toplevel | None

    def __new__(cls, tcltk: TclTk):
        self = super().__new__(cls)
        self.tcltk = py.read_only_attribute(tcltk)
        toplevel = tcltk.tk.winfo_toplevel()
        self._toplevel = py.read_only_attribute(assign_later=True)
        self.is_root = py.read_only_attribute(assign_later=True)
        if isinstance(toplevel, tk.Tk):
            self._toplevel = None
            self.is_root = True
        else:
            self._toplevel = toplevel
            self.is_root = False
        return self
