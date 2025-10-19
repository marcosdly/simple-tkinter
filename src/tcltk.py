from __future__ import annotations
from contextvars import ContextVar
import tkinter as tk
import python_meta as py
from typing import cast

_TCL_ROOT_INTERPRETER: ContextVar[TclTk | None] = ContextVar(
    "_TCL_ROOT_INTERPRETER", default=None
)


class TclTk:
    tk: tk.Tk

    @py.single_eval_cached_property
    def tk(self) -> tk.Tk:
        return tk.Tk()

    @py.single_eval_cached_property
    @classmethod
    def root_interpreter(cls) -> TclTk:
        if _TCL_ROOT_INTERPRETER.get() is None:
            _TCL_ROOT_INTERPRETER.set(cls())
        return cast(TclTk, _TCL_ROOT_INTERPRETER.get())

    def tick(self):
        self.tk.update_idletasks()
        self.tk.update()

    def run(self):
        self.tk.mainloop()
