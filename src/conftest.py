from __future__ import annotations

import pytest


@pytest.fixture(scope="function")
def tk_root():
    import tkinter as tk

    root = tk.Tk()
    yield root
    root.destroy()


@pytest.fixture(scope="function")
def tk_tick(tk_root):
    def _tick():
        tk_root.update_idletasks()
        tk_root.update()

    return _tick
