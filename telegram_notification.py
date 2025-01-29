import logging

from telegram import Bot

import config


async def send_message_to_chat(
    message,
    main_logger,
    pin_message=False,
    mention_user=False,
    parse_mode='HTML',
    telegram_bot_token=config.telegram_bot_token,
    chat_id=config.chat_id,
    user_id=config.user_id
):
    logging.getLogger("telegram").setLevel(logging.WARNING)  # Скроет логи telegram
    logging.getLogger("httpx").setLevel(logging.WARNING)  # Если используется httpx
    logging.getLogger("urllib3").setLevel(logging.WARNING)  # Если используется urllib3
    logging.getLogger("asyncio").setLevel(logging.WARNING)  # Скрывает лишние asyncio логи
    logging.getLogger("httpcore").setLevel(logging.WARNING)  # В случае использования httpcore

    logger = main_logger.getChild('telegram_notification')

    try:
        bot = Bot(token=telegram_bot_token)

        if mention_user and user_id:
            message = f"{message}[\\.](tg://user?id={user_id})"

        sent_message = await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=parse_mode
        )

        if pin_message:
            await bot.pin_chat_message(chat_id=chat_id, message_id=sent_message.message_id)

    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")


async def send_message_to_group(
    message,
    main_logger,
    thread_id=None,
    pin_message=False,
    mention_user=False,
    parse_mode='HTML',
    telegram_bot_token=config.telegram_bot_token,
    chat_id=config.chat_id,
    user_id=config.user_id
):
    logging.getLogger("telegram").setLevel(logging.WARNING)  # Скроет логи telegram
    logging.getLogger("httpx").setLevel(logging.WARNING)  # Если используется httpx
    logging.getLogger("urllib3").setLevel(logging.WARNING)  # Если используется urllib3
    logging.getLogger("asyncio").setLevel(logging.WARNING)  # Скрывает лишние asyncio логи
    logging.getLogger("httpcore").setLevel(logging.WARNING)  # В случае использования httpcore

    logger = main_logger.getChild('telegram_notification')

    try:
        bot = Bot(token=telegram_bot_token)

        if mention_user and user_id:
            message = f"{message}[\\.](tg://user?id={user_id})"

        if thread_id:
            sent_message = await bot.send_message(
                chat_id=chat_id,
                text=message,
                message_thread_id=thread_id,
                parse_mode=parse_mode
            )
        else:
            sent_message = await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=parse_mode
            )

        if pin_message:
            await bot.pin_chat_message(chat_id=chat_id, message_id=sent_message.message_id)

    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")
