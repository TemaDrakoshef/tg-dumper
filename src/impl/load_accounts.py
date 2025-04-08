import asyncio
import os
import shutil
from pathlib import Path
from contextlib import suppress
import uuid

import click
from loguru import logger
import telethon

import opentele
from src.config import APP_HASH, APP_ID, SYSTEM_VERSION
from src.utils import (
    ExitToMenu,
    get_menu,
    get_choice_menu,
    lang,
    pretty_prompt,
)


def make_loading_menu() -> int:
    choices = [
        lang(
            ru="Подгрузить аккаунты с .session-файлов (из `feed_sessions`)",
            en="Load accounts from .session-files (from `feed_sessions`)",
        ),
        lang(
            ru="Подгрузить аккаунты с tdata (из `feed_tdata`)",
            en="Load accounts from tdata (from `feed_tdata`)",
        ),
    ]

    menu = get_menu(
        menu_name=lang(ru="Подгрузка аккаунтов", en="Loading accounts"),
        choices_raw=choices,
        is_description=False,
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


async def load_accounts() -> None:
    menu = make_loading_menu()

    match menu:
        case 1:
            await _load_sessions()
        case 2:
            await _load_tdata()

    raise ExitToMenu()


async def _load_sessions() -> None:
    sem = asyncio.Semaphore(60)

    menu = get_menu(
        menu_name=lang(ru="Подгрузка sessions", en="Loading sessions"),
        choices_raw=None,
        is_description=False,
    )
    click.echo(menu)

    spam_session_files = [
        f.split(".")[0]
        for f in os.listdir("feed_sessions")
        if f.endswith(".session")
    ]
    if not spam_session_files:
        logger.opt(colors=True).error(
            lang(
                ru="Сессии не найдены в папке `feed_sessions`",
                en="No sessions found in the `feed_sessions` folder",
            ),
        )
        raise ExitToMenu()
    logger.opt(colors=True).success(
        lang(
            ru="Найдено <g><n>{count}</n></g> аккаунтов. Подгружаем...",
            en="Found <g><n>{count}</n></g> accounts. Loading...",
        ),
        count=len(spam_session_files),
    )
    with open("accounts.txt", encoding="utf-8") as accounts:
        exist_accounts = set(accounts.read().split())
    exists_accounts_were = len(exist_accounts)
    loading_coroutines = [
        _load_sessions_accounts(spam_session_file, exist_accounts, sem)
        for spam_session_file in spam_session_files
    ]
    new_accounts = await asyncio.gather(*loading_coroutines)
    new_accounts_set = {acc for acc in new_accounts if acc is not None}

    with open("accounts.txt", "w", encoding="utf-8") as new_accounts_file:
        new_accounts_file.write("\n".join(exist_accounts | new_accounts_set))

    logger.opt(colors=True).success(
        lang(
            ru="Удалось подгрузить <n><g>{added}</g></n> новых аккаунтов!",
            en="Loaded <n><g>{added}</g></n> new accounts!",
        ),
        added=len(exist_accounts) - exists_accounts_were,
    )
    raise ExitToMenu()


async def _load_sessions_accounts(
    spam_session_file: str, exist_accounts: set[str], sem: asyncio.Semaphore
) -> None:
    async with sem:
        try:
            session_path = Path("feed_sessions") / spam_session_file

            client = telethon.TelegramClient(
                str(session_path),
                api_id=APP_ID,
                api_hash=str(APP_HASH),
                system_version=SYSTEM_VERSION,
            )

            def raise_error():
                raise ValueError("Require phone sms-code auth")

            try:
                await client.start(phone=raise_error)
                me = await client.get_me()
            finally:
                with suppress(Exception):
                    await client.disconnect()
        except Exception as err:
            logger.opt(colors=True).warning(
                lang(
                    ru="Не удалось подгрузить аккаунт <c>{spam_session_file}</c> по "
                    "причине <r>{err}</r>",
                    en="Cannot load account <c>{spam_session_file}</c> because <r>{"
                    "err}</r>",
                ),
                spam_session_file=spam_session_file,
                err=err,
            )
            os.remove(f"{session_path}.session")
        else:
            with suppress(Exception):
                old_session_path = f"{session_path}.session"
                with open(old_session_path, "rb") as old_session_file:
                    old_session_content = old_session_file.read()

                new_session_path = Path("sessions") / f"{me.phone}.session"
                with open(new_session_path, "wb+") as new_session_file:
                    new_session_file.write(old_session_content)

                exist_accounts.add(me.phone)
                os.remove(old_session_path)

                journal_path = f"{session_path}.session-journal"
                if os.path.exists(journal_path):
                    os.remove(journal_path)

                logger.opt(colors=True).info(
                    lang(
                        ru="Удалось подгрузить аккаунт <c>{spam_session_file}</c>",
                        en="Successfully loaded <c>{spam_session_file}</c> account",
                    ),
                    spam_session_file=spam_session_file,
                )
                return me.phone


async def _load_tdata() -> None:
    ftemp = Path(".tdtemp")
    if not ftemp.exists():
        ftemp.mkdir()
    else:
        shutil.rmtree(ftemp, ignore_errors=True)
        ftemp.mkdir()

    menu = get_menu(
        menu_name=lang(ru="Подгрузка TDATA", en="Loading TDATA"),
        choices_raw=None,
        is_description=False,
    )
    click.echo(menu)

    sem = asyncio.Semaphore(60)
    tdata_paths = [
        f for f in os.listdir("feed_tdata") if Path("feed_tdata", f).is_dir()
    ]

    if not tdata_paths:
        return logger.opt(colors=True).error(
            lang(
                ru="Не найдено ни одной TDATA в `feed_tdata`",
                en="No any TDATA was found in `feed_tdata`",
            )
        )

    logger.opt(colors=True).success(
        lang(
            ru="Найдено <g><n>{count}</n></g> tdata. Подгружаем...",
            en="Found <g><n>{count}</n></g> tdata. Loading...",
        ),
        count=len(tdata_paths),
    )

    converting_tasks = [_load_tdata_account(path, sem) for path in tdata_paths]

    new_phones = await asyncio.gather(*converting_tasks)
    new_phones = {
        new_phone for new_phone in new_phones if new_phone is not None
    }
    with open("accounts.txt", encoding="utf-8") as accounts:
        exist_accounts = set(accounts.read().split())

    with open("accounts.txt", "w", encoding="utf-8") as new_accounts:
        new_accounts.write("\n".join(exist_accounts | new_phones))

    logger.opt(colors=True).success(
        lang(
            ru="Удалось подгрузить <n><g>{added}</g></n> новых аккаунтов!",
            en="Loaded <n><g>{added}</g></n> new accounts!",
        ),
        added=len(new_phones),
    )

    shutil.rmtree(".tdtemp", ignore_errors=True)

    raise ExitToMenu()


async def _load_tdata_account(path: str, sem: asyncio.Semaphore):
    async with sem:
        real_path = Path("feed_tdata", path)
        client = None

        try:
            tdesk = opentele.td.TDesktop(str(real_path), keyFile="data")
            # api = opentele.api.API.TelegramIOS.Generate()

            new_session_path = Path(".tdtemp", uuid.uuid4().hex + ".session")

            client = await tdesk.ToTelethon(
                session=str(new_session_path),
                flag=opentele.api.UseCurrentSession,
                # api=api
            )

            await asyncio.wait_for(client.connect(), timeout=10)
            me = await client.get_me()

            if me is None:
                raise asyncio.TimeoutError()

            await client.disconnect()
            await asyncio.sleep(1)
            shutil.move(
                str(new_session_path),
                new_session_path.parent.parent
                / "sessions"
                / (me.phone + ".session"),
            )
        except asyncio.TimeoutError:
            logger.opt(colors=True).warning(
                lang(
                    ru="Не удалось подключиться к аккаунту <c>{path}</c>",
                    en="Failed to connect to the <c>{path}</c> account",
                ),
                path=str(real_path),
            )
            return None
        except asyncio.TimeoutError:
            logger.opt(colors=True).warning(
                lang(
                    ru="Не удалось подключиться к аккаунту <c>{path}</c>",
                    en="Failed to connect to the <c>{path}</c> account",
                ),
                path=str(real_path),
            )
            return None
        else:
            logger.opt(colors=True).info(
                lang(
                    ru="Удалось подгрузить аккаунт <c>{spam_session_file}</c> ({"
                    "real_path})",
                    en="Successfully loaded <c>{spam_session_file}</c> account ({"
                    "real_path})",
                ),
                spam_session_file=me.phone,
                real_path=str(real_path),
            )
            return me.phone
        finally:
            try:
                if client:
                    if client.is_connected():
                        await client.disconnect()
                await asyncio.sleep(0.5)
                if new_session_path.exists():
                    try:
                        os.remove(new_session_path)
                    except PermissionError:
                        pass
                shutil.rmtree(real_path, ignore_errors=True)
            except Exception as cleanup_err:
                logger.debug(f"Cleanup error: {cleanup_err}")
