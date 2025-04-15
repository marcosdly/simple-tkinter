from __future__ import annotations

from typing import Union, cast
from argparse import Namespace, ArgumentParser


std_styles = [
    "TButton",
    "TCheckbutton",
    "TCombobox",
    "TEntry",
    "TFrame",
    "TLabel",
    "TLabelFrame",
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


def json_dump(obj: object):
    import json

    return json.dumps(obj, indent=2)


def command_list(args: Namespace):
    if args.command == "class":
        print(json_dump(std_styles) if args.json else "\n".join(std_styles))
        exit(0)

    from tkinter import ttk

    s = ttk.Style(None)
    theme_names = s.theme_names()

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
    element_names = cast(tuple[str, ...], s.element_names())  # type: ignore[reportUnknownMemberType]

    if args.command == "elements":
        print(json_dump(element_names) if args.json else "\n".join(element_names))
        exit(0)

    all_options: dict[str, dict[str, Union[str, float]]] = {
        element: {
            option: s.lookup(element, option)  # type: ignore[reportUnknownMemberType]
            for option in cast(tuple[str, ...], s.element_options(element))  # type: ignore[reportUnknownMemberType]
        }
        for element in element_names
    }

    if args.command == "options":
        print(json_dump(all_options))
        exit(0)


def main():
    main_parser = ArgumentParser(prog="tkutil")
    subparsers_factory = main_parser.add_subparsers(
        help="sub-command", dest="subcommand"
    )

    list_subparser = subparsers_factory.add_parser("list")
    _ = list_subparser.add_argument(
        "command", choices=["themes", "elements", "options", "class"]
    )
    _ = list_subparser.add_argument("--json", action="store_true")
    _ = list_subparser.add_argument("--theme", default="default")

    args = main_parser.parse_args()
    if args.subcommand == "list":
        command_list(args)


if __name__ == "__main__":
    main()
