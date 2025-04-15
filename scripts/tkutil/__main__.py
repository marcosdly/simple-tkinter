from __future__ import annotations

from typing import TYPE_CHECKING, cast, no_type_check
from argparse import ArgumentParser


if TYPE_CHECKING:
    from typing import Any, Union
    from tkinter import ttk
    from argparse import Namespace
    from collections.abc import Iterable

    OptionDict = dict[str, Union[str, float]]
    LayoutChild = dict[str, Union[OptionDict, list["LayoutChild"]]]
    TkLayoutDefinition = list[tuple[str, LayoutChild]]
    ParsedLayoutStyle = list[LayoutChild]

std_styles = [
    "TButton",
    "TCheckbutton",
    "TCombobox",
    "TEntry",
    "TFrame",
    "TLabel",
    "TLabelframe",
    "TMenubutton",
    "TNotebook",
    "TPanedwindow",
    "Horizontal.TProgressbar",
    "Vertical.TProgressbar",
    "TRadiobutton",
    "Horizontal.TScale",
    "Vertical.TScale",
    "Horizontal.TScrollbar",
    "Vertical.TScrollbar",
    "TSeparator",
    "TSizegrip",
    "Treeview",
]


def replace_empty_string(strings: "Iterable[str]") -> list[str]:
    _copy = list(strings)
    try:
        i = _copy.index("")
        _copy[i] = "<empty string>"
    except ValueError:
        pass
    return _copy


@no_type_check
def get_options_for_element(s: "ttk.Style", element_name: str) -> "OptionDict":
    return {
        option: s.lookup(element_name, option)
        for option in s.element_options(element_name)
    }


def json_dump(obj: object):
    import json

    return json.dumps(obj, indent=2)


def command_list(args: "Namespace"):
    if args.command == "class":
        print(json_dump(std_styles) if args.json else "\n".join(std_styles))
        exit(0)

    from tkinter import ttk

    s = ttk.Style(None)
    theme_names = replace_empty_string(s.theme_names())

    if args.command == "themes":
        print(json_dump(theme_names) if args.json else "\n".join(theme_names))
        exit(0)

    theme_selected = args.theme.strip()
    if theme_selected not in theme_names:
        print(
            f"ERROR: unknown theme '{theme_selected}'",
            f"Must be one of: {', '.join(theme_names)}",
        )
        exit(1)

    s.theme_use(theme_selected)
    element_names = replace_empty_string(cast(tuple[str, ...], s.element_names()))  # type: ignore[reportUnknownMemberType]

    if args.command == "elements":
        print(json_dump(element_names) if args.json else "\n".join(element_names))
        exit(0)

    if args.command == "options":
        all_options: dict[str, "OptionDict"] = {
            element: get_options_for_element(s, element) for element in element_names
        }

        print(json_dump(all_options))
        exit(0)

    if args.command == "layouts":
        all_layouts: dict[str, list['Any']] = {
            style: s.layout(style)  # type: ignore[reportUnknownMemberType]
            for style in std_styles
        }

        print(json_dump(all_layouts))
        exit(0)

    if args.command == "settings":

        def make_style_settings(layout_def: "TkLayoutDefinition") -> "ParsedLayoutStyle":
            settings_collection: "ParsedLayoutStyle" = []
            for element, settings in layout_def:
                options: "OptionDict" = get_options_for_element(s, element)
                children: "Union[TkLayoutDefinition, None]" = settings.pop(
                    "children", None
                )  # type: ignore[reportAssignmentType]
                settings_collection.append(
                    {  # type: ignore[reportArgumentType]
                        "name": element,
                        "options": options,
                        "layout": settings,
                        "children": make_style_settings(children)
                        if children is not None
                        else [],
                    }
                )
            return settings_collection

        all_layout_settings = {
            layout_name: make_style_settings(
                cast("TkLayoutDefinition", s.layout(layout_name))  # type: ignore[reportUnknownMemberType]
            )
            for layout_name in std_styles
        }

        print(json_dump(all_layout_settings))
        exit(0)


def main():
    main_parser = ArgumentParser(prog="tkutil")
    subparsers_factory = main_parser.add_subparsers(
        help="sub-command", dest="subcommand"
    )

    list_subparser = subparsers_factory.add_parser("list")
    _ = list_subparser.add_argument(
        "command",
        choices=["themes", "elements", "options", "class", "layouts", "settings"],
    )
    _ = list_subparser.add_argument("--json", action="store_true")
    _ = list_subparser.add_argument("--theme", default="default")

    args = main_parser.parse_args()
    if args.subcommand == "list":
        command_list(args)


if __name__ == "__main__":
    main()
