from __future__ import annotations

import python_meta as py

from window import Window

import tkinter as tk

from typing import Callable, cast
from tkinter import ttk
from contextvars import ContextVar


_TCL_ROOT_INTERPRETER: ContextVar[TclTk | None] = ContextVar(
    "_TCL_ROOT_INTERPRETER", default=None
)
_TTK_ROOT_STYLE_DB: ContextVar[ttk.Style | None] = ContextVar(
    "_TTK_ROOT_STYLE_DB", default=None
)
_TK_MASTER_WINDOW: ContextVar[Window | None] = ContextVar(
    "_TK_MASTER_WINDOW", default=None
)


class TclTk:
    """God object for the Tcl/Tk interpreter."""

    tk: tk.Tk
    is_root: bool

    def _get_default_root(self) -> tk.Tk:
        """Get the default root Tk instance using tkinter internal utility."""
        # Internal library utility to access default root Tk instance
        # NOTE: Can be suppressed by calling tk.NoDefaultRoot()
        get_default_root: Callable[[], tk.Tk] = tk._get_default_root  # pyright: ignore[reportAttributeAccessIssue]
        try:
            return get_default_root()
        except RuntimeError as e:
            raise RuntimeError("Failed to get default root Tk instance") from e

    def __new__(cls):
        self = super().__new__(cls)
        is_root: bool = False
        if _TCL_ROOT_INTERPRETER.get() is None:
            # First instance created becomes the root interpreter
            is_root = True
            _TCL_ROOT_INTERPRETER.set(self)
        self.is_root = py.read_only_attribute(is_root)
        return self

    @py.single_eval_cached_property
    def tk(self) -> tk.Tk:
        if self.is_root:
            return self._get_default_root()
        return tk.Tk()

    @py.single_eval_cached_property
    @classmethod
    def root_interpreter(cls) -> TclTk:
        if _TCL_ROOT_INTERPRETER.get() is None:
            # First instance created becomes the root interpreter
            _ = cls()
        return cast(TclTk, _TCL_ROOT_INTERPRETER.get())

    @py.single_eval_cached_property
    def root_style_db(self) -> ttk.Style:
        # Creating a style DB will create a window if none exists yet
        # Make sure there's a master window first
        window = self.master_window
        if _TTK_ROOT_STYLE_DB.get() is None:
            # NOTE: master=None falls back to the same default root returned
            # by self._get_default_root()
            toplevel: tk.Toplevel | None = window._toplevel
            _TTK_ROOT_STYLE_DB.set(ttk.Style(master=toplevel))
        return cast(ttk.Style, _TTK_ROOT_STYLE_DB.get())

    @py.single_eval_cached_property
    def master_window(self) -> Window:
        if _TK_MASTER_WINDOW.get() is None:
            _TK_MASTER_WINDOW.set(Window(TclTk.root_interpreter))
        return cast(Window, _TK_MASTER_WINDOW.get())

    def tick(self):
        self.tk.update_idletasks()
        self.tk.update()

    def run(self):
        self.tk.mainloop()
