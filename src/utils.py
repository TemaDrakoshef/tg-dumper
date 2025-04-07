import sys
import traceback
from os import get_terminal_size
from typing import TypeVar

import click
import loguru

from src.config import CURRENT_LANG


_LOGO_RAW = """
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
_LOGO_CENTERED = (
    "\n"
    + "\n".join(
        line.center(terminal_width) for line in _LOGO_RAW.strip().split("\n")
    )
    + "\n\n"
)
logo = click.style(_LOGO_CENTERED, fg="green")


class ExitToMenu(Exception):
    pass


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
    choices_raw: list[tuple[str, str]] | None = None,
    is_description: bool = False,
):
    row = "[{0}] {1}: {2}" if is_description else "[{0}] {1}"
    choices = ""
    if choices_raw:
        choices = "\n".join(
            row.format(
                click.style(str(ind), fg="yellow"),
                click.style(
                    choice[0] if is_description else choice, fg="magenta"
                ),
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
    click.clear()

    return menu_choice


def setup_logging():
    loguru.logger.remove()
    loguru.logger.add(
        sys.stdout,
        format="<lvl>[</lvl><c>{time:HH:mm:ss.SSS}</c><lvl>]</lvl> <lvl>{message}</lvl>",
    )


def return_to_menu(err=None):
    if not isinstance(
        err,
        (
            ExitToMenu,
            KeyboardInterrupt,
            click.exceptions.Abort,
        ),
    ):
        traceback.print_exc()

    sep_line = click.style("━" * terminal_width, fg="bright_black")
    arrows = click.style(">" * 3, fg="red")
    return_prompt = click.style(
        lang(
            ru="Вернуться в меню? [y/n]",
            en="Return to menu? [y/n]",
        ),
        fg="cyan",
    )
    prompt = "\n{}\n{} {}".format(sep_line, arrows, return_prompt)
    click.echo(prompt, nl=False)
    return_to_menu_char = click.getchar()
    if return_to_menu_char.lower() == "n":
        click.secho(
            lang(ru="\nЗавершение работы", en="Shutdown RobGram"),
            fg="green",
        )
        sys.exit(1)
