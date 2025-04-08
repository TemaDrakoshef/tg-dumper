import asyncio
import click
from src.impl.dumper import dumper_menu
from src.impl.load_accounts import load_accounts
from src.utils import get_choice_menu, get_menu, lang, pretty_prompt


def make_home_menu():
    choices = [
        (
            lang(ru="Дампер", en="Dumper"),
            lang(
                ru="Извлечь диалоги и их содержимое с аккаунтов",
                en="Extract dialogs and their contents from accounts",
            ),
        ),
        (
            lang(ru="Подгрузить аккаунты", en="Load accounts"),
            lang(
                ru="Добавить в используемые аккаунты готовые .session-файлы или tdata",
                en="Add .session-files or tdata for used accounts",
            ),
        ),
    ]

    menu = get_menu(
        menu_name=lang(ru="Главное меню", en="Main menu"),
        choices_raw=choices,
        is_description=True,
    )
    click.echo(menu)

    text_tip = pretty_prompt(
        lang(
            ru="Выберите пункт меню",
            en="Type the number of a needed paragraph",
        )
    )
    menu_choice = get_choice_menu(text_tip)

    return menu_choice


def home_page(config: dict):
    loop = asyncio.new_event_loop()
    menu_choice = make_home_menu()

    match menu_choice:
        case 1:
            loop.run_until_complete(dumper_menu(config))
        case 2:
            loop.run_until_complete(load_accounts())
