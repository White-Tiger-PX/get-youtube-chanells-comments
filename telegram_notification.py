from telegram import Bot

import config


async def send_message_to_thread(
    message,
    thread_id,
    main_logger,
    pin_message=False,
    mention_user=False,
    parse_mode='HTML',
    telegram_bot_token=config.telegram_bot_token,
    chat_id=config.chat_id,
    user_id=config.user_id
):
    logger = main_logger.getChild('telegram_notification')

    try:
        bot = Bot(token=telegram_bot_token)

        if mention_user and user_id:
            message = f"{message}[\\.](tg://user?id={user_id})"

        sent_message = await bot.send_message(
            chat_id=chat_id,
            text=message,
            message_thread_id=thread_id,
            parse_mode=parse_mode
        )

        # Если указано, что сообщение нужно закрепить
        if pin_message:
            await bot.pin_chat_message(chat_id=chat_id, message_id=sent_message.message_id)

    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")


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

        # Если указано, что сообщение нужно закрепить
        if pin_message:
            await bot.pin_chat_message(chat_id=chat_id, message_id=sent_message.message_id)

    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")
