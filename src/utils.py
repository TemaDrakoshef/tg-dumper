from os import get_terminal_size
from typing import TypeVar
import click


_logo_raw = """
▄▄▄█████▓  ▄████ ▓█████▄  █    ██  ███▄ ▄███▓ ██▓███  ▓█████  ██▀███  
▓  ██▒ ▓▒ ██▒ ▀█▒▒██▀ ██▌ ██  ▓██▒▓██▒▀█▀ ██▒▓██░  ██▒▓█   ▀ ▓██ ▒ ██▒
▒ ▓██░ ▒░▒██░▄▄▄░░██   █▌▓██  ▒██░▓██    ▓██░▓██░ ██▓▒▒███   ▓██ ░▄█ ▒
░ ▓██▓ ░ ░▓█  ██▓░▓█▄   ▌▓▓█  ░██░▒██    ▒██ ▒██▄█▓▒ ▒▒▓█  ▄ ▒██▀▀█▄  
  ▒██▒ ░ ░▒▓███▀▒░▒████▓ ▒▒█████▓ ▒██▒   ░██▒▒██▒ ░  ░░▒████▒░██▓ ▒██▒
  ▒ ░░    ░▒   ▒  ▒▒▓  ▒ ░▒▓▒ ▒ ▒ ░ ▒░   ░  ░▒▓▒░ ░  ░░░ ▒░ ░░ ▒▓ ░▒▓░
    ░      ░   ░  ░ ▒  ▒ ░░▒░ ░ ░ ░  ░      ░░▒ ░      ░ ░  ░  ░▒ ░ ▒░
  ░      ░ ░   ░  ░ ░  ░  ░░░ ░ ░ ░      ░   ░░          ░     ░░   ░ 
               ░    ░       ░            ░               ░  ░   ░     
                  ░                                                   
        """

terminal_width = get_terminal_size().columns
_logo_centered = (
    "\n"
    + "\n".join(
        line.center(terminal_width) for line in _logo_raw.strip().split("\n")
    )
    + "\n\n"
)
logo = click.style(_logo_centered, fg="green")

CURRENT_LANG: str = "ru"


def pretty_prompt(text: str):
    prompt_prefix = (
        click.style("[", fg="cyan")
        + click.style("#", fg="red")
        + click.style("]", fg="cyan")
    )
    return f"{prompt_prefix} {text}\n"


T = TypeVar("T")


def lang(*, ru: T, en: T) -> T:
    if CURRENT_LANG == "ru":
        return ru
    else:
        return en


def get_menu(
    menu_name: str,
    choices_raw: list[tuple[str, str]],
    is_description: bool = False,
):
    row = "[{0}] {1}: {2}" if is_description else "[{0}] {1}"
    choices = "\n".join(
        row.format(
            click.style(str(ind), fg="yellow"),
            click.style(choice[0], fg="magenta"),
            click.style(choice[1], fg="cyan") if is_description else None,
        )
        for ind, choice in enumerate(choices_raw, 1)
    )
    choices = click.style(choices, fg="reset")

    menu = "\n {menu_name}\n\n\b{choices}\n\n".strip().format(
        choices=choices,
        menu_name=format(
            f" [ {menu_name} ] ",
            f"━^{terminal_width}",
        ),
    )

    click.clear()
    menu = click.style(menu, fg="green")
    menu = logo + menu

    return menu


def get_choice_menu(text: str):
    menu_choice = click.prompt(
        "\n{}\n".format("━" * terminal_width) + text,
        type=int,
        prompt_suffix="> ",
    )
    # click.clear()

    return menu_choice
