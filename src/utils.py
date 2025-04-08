import asyncio
from pathlib import Path
import random
import sys
import traceback
from os import get_terminal_size
from typing import TypeVar, List

import click
from loguru import logger
import telethon

from src.config import APP_HASH, APP_ID, CURRENT_LANG, SYSTEM_VERSION


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

logged_accounts: List[telethon.TelegramClient] = []


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
    logger.remove()
    logger.add(
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


async def make_telegram_client(
    phone_number: str, config: dict, skip_code_callback: bool = True
) -> telethon.TelegramClient:
    """
    Creates a session for a specific account. If the account is blocked, offers to delete it
    """

    def code_callback():
        if skip_code_callback:
            return None

        return click.prompt(
            lang(
                ru=f"Введите код подтверждения, пришедший на номер `{phone_number}` (отправлен и в телеграмме, и по смс)",
                en=f"Enter confirmation code for number `{phone_number}` (sent in telegram and by sms)",
            )
        )

    session_path = Path("sessions") / f"{phone_number}.session"

    if config["proxies"]:
        for proxy in random.sample(
            config["proxies"].copy(), len(config["proxies"])
        ):
            client = telethon.TelegramClient(
                str(session_path),
                api_id=APP_ID,
                api_hash=str(APP_HASH),
                proxy=proxy,
                lang_code=config["lang"],
                system_lang_code=config["lang"],
                system_version=SYSTEM_VERSION,
            )
            try:
                await client.start(
                    phone=lambda: str(phone_number),
                    code_callback=code_callback,
                    max_attempts=1,
                )
                client.phone = phone_number
            except ConnectionError:
                logger.opt(colors=True).error(
                    lang(
                        ru=f"Не удалось подключиться к прокси <le>{proxy['addr']}</le>",
                        en=f"Can't connect to a proxy <le>{proxy['addr']}</le>",
                    ),
                )
                config["proxies"].remove(proxy)
                await client.disconnect()
            else:
                # Move the proxy to the end to use other proxies
                config["proxies"].remove(proxy)
                config["proxies"].append(proxy)
                logger.opt(colors=True).success(
                    lang(
                        ru=f"Удалось подключиться к прокси! Используется "
                        f"<le>{proxy['addr']}</le> для "
                        f"номера <le>{phone_number}</le>",
                        en=f"Connection has been established with proxy "
                        f"<le>{proxy['addr']}</le> and phone number "
                        f"<le>{phone_number}</le>",
                    ),
                )
                return client
        click.secho(
            lang(
                ru="Не удалось подключиться ни к одному из прокси",
                en="Can't connect to any proxies",
            ),
            fg="red",
        )
        sys.exit(1)
    else:
        client = telethon.TelegramClient(
            str(session_path),
            api_id=APP_ID,
            api_hash=str(APP_HASH),
            lang_code=config["lang"],
            system_lang_code=config["lang"],
            system_version=SYSTEM_VERSION,
        )

        await client.start(
            phone=lambda: str(phone_number),
            # code_callback=code_callback,
            max_attempts=1,
        )
        client.phone = phone_number
        logged_accounts.append(client)
        return client


async def connect_account(
    phone_number,
    config,
    remain_phones,
    accounts_clients,
):
    try:
        client = await make_telegram_client(phone_number, config)
    except Exception:
        with open("registration.err", "w+", encoding="utf-8") as err_log:
            traceback.print_exc(file=err_log)

        logger.opt(colors=True).error(
            lang(
                ru=f"Невозможно войти в аккаунт `{phone_number}`, похоже, что аккаунт был заблокирован",
                en=f"Can't sign in into account `{phone_number}`, looks like account has been banned",
            ),
        )

        remain_phones.remove(phone_number)
    else:
        accounts_clients.append(client)


async def fetch_clients(config: dict):
    accounts_clients = []
    try:
        with open("accounts.txt", encoding="utf-8") as accounts:
            phone_numbers = accounts.read().split()
            remain_phones = phone_numbers.copy()

            connection_coroutines = [
                connect_account(
                    phone_number, config, remain_phones, accounts_clients
                )
                for phone_number in phone_numbers
            ]
            await asyncio.gather(*connection_coroutines)

        with open("accounts.txt", "w", encoding="utf-8") as accounts:
            accounts.write("\n".join(remain_phones))

        if not accounts_clients:
            click.echo(
                lang(
                    ru="Для работы программы необходим хотя бы один аккаунт. "
                    "Добавьте номер телефона в файл {accounts}",
                    en="Require at least one account. "
                    "Add an accounts' phone to {accounts}",
                ).format(accounts=click.style("accounts.txt", fg="cyan"))
            )
            raise ExitToMenu()
    except Exception as err:
        await asyncio.gather(
            *[client.disconnect() for client in accounts_clients]
        )
        raise err

    logger.opt(colors=True).info(
        lang(
            ru="Удалось подгрузить <n><g>{accounts}</g></n> аккаунтов",
            en="Loaded <n><g>{accounts}</g></n> accounts!",
        ),
        accounts=len(accounts_clients),
    )
    return accounts_clients
