import asyncio
from pathlib import Path
import datetime

import click
from loguru import logger
from telethon import TelegramClient
from telethon.tl import types
from jinja2 import Environment, FileSystemLoader

from src.utils import ExitToMenu, fetch_clients, get_menu, lang


async def dumper_menu(config: dict):
    menu = get_menu(
        menu_name=lang(ru="Дампер", en="Дампер"),
        choices_raw=None,
        is_description=False,
    )
    click.echo(menu)

    sem = asyncio.Semaphore(60)
    clients = await fetch_clients(config)

    try:
        balance_tasks = []
        for account in clients:
            balance_tasks.append(_dumper(client=account, sem=sem))

        await asyncio.gather(*balance_tasks)
    except Exception as err:
        logger.exception(err)
    finally:
        await asyncio.gather(*[client.disconnect() for client in clients])
        raise ExitToMenu()


async def _dumper(client: TelegramClient, sem: asyncio.Semaphore):
    async with sem:
        dialogs = await client.get_dialogs()
        me = await client.get_me()

        logger.opt(colors=True).info(
            lang(
                ru=f"Найдено <n><g>{len(dialogs)}</g></n> диалогов на аккаунте <n><g>{me.phone}</g></n>",
                en=f"Found <n><g>{len(dialogs)}</g></n> dialogs on account <n><g>{me.phone}</g></n>",
            )
        )

        for dialog in dialogs:
            if not dialog.is_user:
                continue

            logger.opt(colors=True).info(
                lang(
                    ru=f"Начало обработки диалога: <n><c>{dialog.name}</c></n>",
                    en=f"Start of dialog processing: <n><c>{dialog.name}</c></n>",
                ),
            )

            await export_dialog(client, dialog)


async def export_dialog(client: TelegramClient, dialog: types.Dialog):
    me = await client.get_me()
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("dialog_template.html")

    safe_name = sanitize_filename(f"{dialog.name}", dialog.entity.id)
    export_dir = Path(f"exports/{me.phone}/{safe_name}")
    export_dir.mkdir(parents=True, exist_ok=True)
    (export_dir / "css").mkdir(exist_ok=True)
    (export_dir / "js").mkdir(exist_ok=True)
    (export_dir / "media").mkdir(exist_ok=True)
    (export_dir / "media" / ".thumb").mkdir(exist_ok=True)
    copy_static_files(export_dir)

    messages = []
    async for message in client.iter_messages(dialog.entity):
        messages.append(message)
        if len(messages) % 100 == 0:
            logger.opt(colors=True).info(
                lang(
                    ru=f"Диалог <c>{dialog.name}</c>: Получено <c>{len(messages)}</c> сообщений",
                    en=f"Dialog <c>{dialog.name}</c>: Received <c>{len(messages)}</c> messages",
                )
            )

        if message.media:
            await download_media(client, message, export_dir)

    logger.opt(colors=True).info(
        lang(
            ru=f"Диалог <c>{dialog.name}</c>: Получено <c>{len(messages)}</c> сообщений",
            en=f"Dialog <c>{dialog.name}</c>: Received <c>{len(messages)}</c> messages",
        )
    )

    html_content = template.render(
        dialog=dialog,
        messages=messages,
        me=me,
        format_date=format_date,
        get_sender_initial=get_sender_initial,
        download_media=lambda: download_media(client, message, export_dir),
    )

    with open(export_dir / "messages.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.opt(colors=True).success(
        lang(
            ru=f"Диалог <c>{dialog.name}</c> сохранен в папку `<c>{export_dir}</c>`",
            en=f"Dialog <c>{dialog.name}</c> is saved in the `<c>{export_dir}</c>` folder",
        )
    )


def sanitize_filename(name: str, chat_id: int) -> str:
    # raw_filename = "".join(c if c.isalnum() else '_' for c in name)
    # raw_filename = raw_filename.replace("__", "").replace(".", "").replace(" ", "_")
    filename = f"{chat_id} {format_date(datetime.datetime.now())}"
    return filename.replace(":", "-").replace(".", "-")


def format_date(date: datetime.datetime) -> str:
    return date.strftime("%d.%m.%Y %H:%M")


async def download_media(
    client: TelegramClient, message: types.Message, export_dir: Path
):
    if not message.media:
        return None

    media_dir = export_dir / "media"
    if isinstance(message.media, types.MessageMediaPhoto):
        filename = f"photo_{message.id}.jpg"
        path = media_dir / "photos" / filename
        await client.download_media(message.media, file=path)

        thumbnail_path = media_dir / ".thumb" / filename
        for size in message.media.photo.sizes:
            if isinstance(size, (types.PhotoSize, types.PhotoSizeProgressive)):
                if size.type == "m":
                    await client.download_media(
                        message.media, thumb=size, file=thumbnail_path
                    )
                    break
        return path

    return None


def copy_static_files(export_dir: Path):
    static_files = {
        "css/style.css": "templates/css/style.css",
        "js/script.js": "templates/js/script.js",
    }

    for dest, src in static_files.items():
        with open(src, "rb") as src_file:
            (export_dir / dest).write_bytes(src_file.read())


def get_sender_initial(message: types.Message):
    sender = message.sender
    if not sender:
        return "?"
    return (
        sender.first_name[0]
        if sender.first_name
        else sender.username[0]
        if sender.username
        else "?"
    ).upper()
