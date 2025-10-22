from __future__ import annotations


def test_bootstrapping_tcltk() -> None:
    from src.tcltk import TclTk

    tcltk = TclTk()
    assert tcltk is TclTk.get_master_interpreter()
    assert TclTk.get_master_style_db()
    assert TclTk.get_master_window()
    FPS = 60
    # Simulate ticking for 10 seconds
    for _ in range(FPS * 10):
        tcltk.tick()


def test_instance_id_registry() -> None:
    from src.tcltk import TclTk
    from src.widget import Widget
    from src.window import Window
    from src.state_managers.instance_id import (
        register_instance_id,
        is_instance_registered,
        get_registered_instance_id,
    )

    tcltk = TclTk()

    w1 = Window(tcltk)
    w2 = Window(tcltk)
    assert register_instance_id(w1) != register_instance_id(w2)

    wid1 = register_instance_id(w1)
    wid2 = register_instance_id(w2)
    assert get_registered_instance_id(w1) == wid1
    assert get_registered_instance_id(w2) == wid2

    wt1 = Widget(w1)
    wt2 = Widget(w1)
    wt3 = Widget(w2)
    assert register_instance_id(wt1) != register_instance_id(wt2)
    assert register_instance_id(wt1) != register_instance_id(wt3)

    assert is_instance_registered(w1)
    assert is_instance_registered(w2)
    assert is_instance_registered(wt1)
    assert is_instance_registered(wt2)
    assert is_instance_registered(wt3)
