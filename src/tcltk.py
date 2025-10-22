from __future__ import annotations

import src.python_meta as py

from src.window import Window

import tkinter as tk

from typing import Callable, cast
from tkinter import ttk
from functools import cache
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


def _get_default_root() -> tk.Tk:
    """Get the default root Tk instance using tkinter internal utility."""
    # Internal library utility to access default root Tk instance
    # NOTE: Can be suppressed by calling tk.NoDefaultRoot()
    get_default_root: Callable[[], tk.Tk] = tk._get_default_root  # pyright: ignore[reportAttributeAccessIssue]
    try:
        return get_default_root()
    except RuntimeError as e:
        raise RuntimeError("Failed to get default root Tk instance") from e


class TclTk:
    """God object for the Tcl/Tk interpreter."""

    is_root: bool

    def __new__(cls):
        self = super().__new__(cls)
        if _TCL_ROOT_INTERPRETER.get() is None:
            # First instance created becomes the root interpreter
            _TCL_ROOT_INTERPRETER.set(self)
        self.is_root = _TCL_ROOT_INTERPRETER.get() is self
        return self

    @property
    @cache
    def tk(self) -> tk.Tk:
        if self.is_root:
            return _get_default_root()
        return tk.Tk()

    @classmethod
    def get_master_interpreter(cls) -> TclTk:
        interpreter = _TCL_ROOT_INTERPRETER.get()
        if interpreter is None:
            # First instance created becomes the root interpreter
            _ = cls()
        return cast(TclTk, interpreter)

    @classmethod
    def get_master_style_db(cls) -> ttk.Style:
        # Creating a style DB will create a window if none exists yet
        # Make sure there's a master window first
        window = cls.get_master_window()
        s = _TTK_ROOT_STYLE_DB.get()
        if s is None:
            # NOTE: master=None falls back to the same default root returned
            # by self._get_default_root()
            toplevel: tk.Toplevel | None = window.toplevel
            s = ttk.Style(master=toplevel)
            _TTK_ROOT_STYLE_DB.set(s)
        return cast(ttk.Style, s)

    @classmethod
    def get_master_window(cls) -> Window:
        window = _TK_MASTER_WINDOW.get()
        if window is None:
            window = Window(cls.get_master_interpreter())
            _TK_MASTER_WINDOW.set(window)
        return cast(Window, window)

    def tick(self):
        self.tk.update_idletasks()
        self.tk.update()

    def run(self):
        self.tk.mainloop()
