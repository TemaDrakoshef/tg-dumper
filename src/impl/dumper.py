import asyncio
import click
from loguru import logger
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument, Message

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
    finally:
        await asyncio.gather(*[client.disconnect() for client in clients])
        raise ExitToMenu()


async def _dumper(client: TelegramClient, sem: asyncio.Semaphore):
    async with sem:
        dialogs = await client.get_dialogs()
        me = await client.get_me()

        logger.opt(colors=True).info(
            lang(
                ru="Найдено <n><g>{dialogs}</g></n> диалогов на аккаунте <n><g>{phone_number}</g></n>",
                en="Found <n><g>{dialogs}</g></n> dialogs on account <n><g>{phone_number}</g></n>",
            ),
            dialogs=len(dialogs),
            phone_number=me.phone,
        )

        result = {"dialogs": [], "messages": []}
        for idx, dialog in enumerate(dialogs, 1):
            if dialog.is_group or dialog.is_channel:
                continue

            dialog_data = await process_dialog(
                client, dialog, idx, len(dialogs)
            )
            if not dialog_data:
                continue

            result["dialogs"].append(
                {
                    "id": dialog_data["dialog_id"],
                    "name": dialog_data["name"],
                    "total_messages": len(dialog_data["messages"]),
                }
            )
            for msg in dialog_data["messages"]:
                msg["dialog_id"] = dialog_data["dialog_id"]
                result["messages"].append(msg)
        logger.opt(colors=True).success(
            lang(
                ru="Итого сохранено: <n><g>{messages}</g></n> сообщений",
                en="Total saved: <n><g>{messages}</g></n> messages",
            ),
            messages=len(result["messages"]),
        )


async def process_dialog(
    client: TelegramClient, dialog, dialog_index: int, total_dialogs: int
) -> dict:
    """Processing a dialog with pagination via client.get_messages"""

    logger.opt(colors=True).info(
        lang(
            ru="[<c>{dialog_index}</c>/<c>{total_dialogs}</c>] Начало обработки диалога: <n><c>{dialog_name}</c></n>",
            en="[<c>{dialog_index}</c>/<c>{total_dialogs}</c>] Start of dialog processing: <n><c>{dialog_name}</c></n>",
        ),
        dialog_index=dialog_index,
        total_dialogs=total_dialogs,
        dialog_name=dialog.name,
    )

    all_messages = []
    offset = 0
    limit = 500
    total_processed = 0

    try:
        while True:
            messages = await client.get_messages(
                dialog.entity, limit=limit, add_offset=offset, reverse=False
            )
            if len(messages) <= 2:
                logger.opt(colors=True).info(
                    lang(
                        ru="Диалог <c>{dialog_name}</c>: Сообщения закончились",
                        en="Dialog <c>{dialog_name}</c>: Messages have run out",
                    ),
                    dialog_name=dialog.name,
                )
                break
            valid_messages = [
                msg for msg in messages if isinstance(msg, Message)
            ]
            received = len(valid_messages)
            if received == 0:
                pass
            
            total_processed += received
            offset += received

            logger.opt(colors=True).info(
                lang(
                    ru=f"Диалог <c>{dialog.name}</c>: Получено {received} сообщений (Всего: {total_processed})",
                    en=f"Dialog <c>{dialog.name}</c>: Received {received} messages (Total: {total_processed})",
                )
            )

            semaphore = asyncio.Semaphore(200)

            async def _process(msg):
                async with semaphore:
                    return await process_message(msg)

            results = await asyncio.gather(
                *(_process(msg) for msg in valid_messages),
                return_exceptions=True,
            )
            
            processed_messages = [
                msg
                for msg in results
                if not isinstance(msg, Exception) and msg is not None
            ]

            all_messages.extend(processed_messages)
            await asyncio.sleep(1.5)

    except Exception as e:
        logger.opt(colors=True).error(
            lang(
                ru="[<c>{dialog_index}</c>/<c>{total_dialogs}</c>] Ошибка в диалоге <n><white>{dialog_name}</white></n>: {exception}",
                en="[<c>{dialog_index}</c>/<c>{total_dialogs}</c>] Error in dialog <n><white>{dialog_name}</white></n>: {exception}",
            ),
            dialog_index=dialog_index,
            total_dialogs=total_dialogs,
            dialog_name=dialog.name,
            exception=str(e),
        )
        return None

    logger.opt(colors=True).success(
        lang(
            ru="Диалог {dialog_name}: Обработано <n><white>{all_messages}</white></n> сообщений",
            en="Dialog {dialog_name}: <n><white>{all_messages}</white></n> messages processed",
        ),
        dialog_name=dialog.name,
        all_messages=len(all_messages),
    )

    return {
        "dialog_id": dialog.id,
        "name": dialog.name,
        "messages": all_messages,
    }


async def process_message(message: Message) -> dict:
    """Processing a single message"""
    media_info = None
    try:
        if message.media:
            if isinstance(message.media, MessageMediaPhoto):
                media_type = "photo"
                media_data = {"id": message.media.photo.id}
            elif isinstance(message.media, MessageMediaDocument):
                doc = message.media.document
                media_type = doc.mime_type.split("/")[0]
                media_data = {
                    "id": doc.id,
                    "mime": doc.mime_type.split("/")[-1],
                    "size": doc.size,
                }
            else:
                media_type = "other"
                media_data = str(message.media)

            media_info = {"type": media_type, "data": media_data}
    except Exception as e:
        logger.warning(f"Ошибка обработки медиа: {str(e)}")

    logger.opt(colors=True).success(f"Обработано сообщение: {message.id}")

    return {
        "id": message.id,
        "text": message.text[:500] if message.text else None,
        "date": message.date.isoformat(),
        "media": media_info,
    }