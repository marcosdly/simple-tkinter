from __future__ import annotations

import pytest

import types
import tkinter as tk
import tkinter.font as __tk_font


@pytest.fixture(scope="class")
def tk_root() -> tk.Tk:
    # 1. `tk.Tk()` is the base class for the tcl interpreter and tk library
    # 2. `tk.Tcl()` is a helper that calls `tk.Tk()` with the most relevant
    # parameters if just want an interpreter instance, but not to load tk
    # 3. Simply gaze over the definition of both to infer that the above true

    return tk.Tk()


@pytest.fixture(scope="function")
def tk_font(tk_root: tk.Tk) -> types.ModuleType:
    _ = tk_root
    return __tk_font


class TestFontAliasNameAllowedCharacters:
    """Individual tests so fails look like issues rather than red flags."""

    def test_dot(self, tk_font: types.ModuleType):
        tk_font.Font(name="example.test")

    def test_whitespace(self, tk_font: types.ModuleType):
        tk_font.Font(name="example test")

    def test_hash(self, tk_font: types.ModuleType):
        tk_font.Font(name="example#test")

    def test_colon(self, tk_font: types.ModuleType):
        tk_font.Font(name="example:test")

    def test_digit(self, tk_font: types.ModuleType):
        for i in range(10):
            tk_font.Font(name=f"example{i}test")

    def test_underscore(self, tk_font: types.ModuleType):
        tk_font.Font(name="example_test")

    def test_hyphen(self, tk_font: types.ModuleType):
        tk_font.Font(name="example-test")

    def test_at(self, tk_font: types.ModuleType):
        tk_font.Font(name="example@test")

    def test_comma(self, tk_font: types.ModuleType):
        tk_font.Font(name="example,test")

    def test_semicolon(self, tk_font: types.ModuleType):
        tk_font.Font(name="example;test")

    def test_equal(self, tk_font: types.ModuleType):
        tk_font.Font(name="example=test")

    def test_slash_forward(self, tk_font: types.ModuleType):
        tk_font.Font(name="example/test")

    def test_dollar(self, tk_font: types.ModuleType):
        tk_font.Font(name="example$test")

    def test_question(self, tk_font: types.ModuleType):
        tk_font.Font(name="example?test")

    def test_percent(self, tk_font: types.ModuleType):
        tk_font.Font(name="example%test")

    def test_star(self, tk_font: types.ModuleType):
        tk_font.Font(name="example*test")

    def test_hat(self, tk_font: types.ModuleType):
        tk_font.Font(name="example^test")

