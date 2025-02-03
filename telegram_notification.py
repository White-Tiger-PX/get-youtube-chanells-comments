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
    """
    Отправляет сообщение в чат Telegram.

    Если параметр `mention_user` установлен в `True`, добавляется упоминание пользователя в сообщении.
    Если параметр `pin_message` установлен в `True`, сообщение будет закреплено.

    Args:
        message (str): Текст сообщения.
        main_logger (logging.Logger): Основной логгер.
        pin_message (bool, optional): Если True, сообщение будет закреплено. По умолчанию False.
        mention_user (bool, optional): Если True, добавляется упоминание пользователя. По умолчанию False.
        parse_mode (str, optional): Режим форматирования текста (HTML или Markdown). По умолчанию 'HTML'.
        telegram_bot_token (str, optional): Токен бота Telegram. По умолчанию берется из конфигурации.
        chat_id (str, optional): Идентификатор чата для отправки сообщения. По умолчанию берется из конфигурации.
        user_id (str, optional): Идентификатор пользователя для упоминания. По умолчанию берется из конфигурации.

    Raises:
        Exception: Если возникает ошибка при отправке сообщения.
    """
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

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
    except Exception as err:
        logger.error("Неизвестная ошибка при открытии URL: %s", err)


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
    """
    Отправляет сообщение в группу Telegram, с возможностью выбора тему (топик).

    Если параметр `mention_user` установлен в `True`, добавляется упоминание пользователя в сообщении.
    Если параметр `pin_message` установлен в `True`, сообщение будет закреплено.
    Если параметр `thread_id` указан, сообщение будет отправлено в определенныую тему.

    Args:
        message (str): Текст сообщения.
        main_logger (logging.Logger): Основной логгер.
        thread_id (str, optional): Идентификатор потока для отправки сообщения. По умолчанию None.
        pin_message (bool, optional): Если True, сообщение будет закреплено. По умолчанию False.
        mention_user (bool, optional): Если True, добавляется упоминание пользователя. По умолчанию False.
        parse_mode (str, optional): Режим форматирования текста (HTML или Markdown). По умолчанию 'HTML'.
        telegram_bot_token (str, optional): Токен бота Telegram. По умолчанию берется из конфигурации.
        chat_id (str, optional): Идентификатор чата для отправки сообщения. По умолчанию берется из конфигурации.
        user_id (str, optional): Идентификатор пользователя для упоминания. По умолчанию берется из конфигурации.

    Raises:
        Exception: Если возникает ошибка при отправке сообщения.
    """
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

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
    except Exception as err:
        logger.error("Неизвестная ошибка при открытии URL: %s", err)
