from __future__ import annotations
import tkinter as tk
import python_meta as py


class Window:
    tk: tk.Tk
    is_root: bool
    _toplevel: tk.Toplevel | None

    def __new__(cls, _tk: tk.Tk):
        self = super().__new__(cls)
        self.tk = py.read_only_attribute(_tk)
        toplevel = _tk.winfo_toplevel()
        self._toplevel = py.read_only_attribute(assign_later=True)
        self.is_root = py.read_only_attribute(assign_later=True)
        if isinstance(toplevel, tk.Tk):
            self._toplevel = None
            self.is_root = True
        else:
            self._toplevel = toplevel
            self.is_root = False
        return self
