from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters
)

import config


async def start(update: Update):
    """
    Обрабатывает команду /start или текстовое сообщение от пользователя или канала.

    Если сообщение отправил пользователь, бот отвечает с `chat_id`, `user_id` и, если доступно, `thread_id`.
    Если сообщение пришло из канала, оно просто выводится в консоль.

    Args:
        update (telegram.Update): Объект обновления, содержащий данные о сообщении.

    Returns:
        None
    """
    chat_id = update.effective_chat.id

    # Проверка на тип источника сообщения
    if update.effective_user:  # Сообщение от пользователя в группе / боту
        user_id = update.effective_user.id
        message_text = update.message.text

        thread_id = getattr(update.message, 'message_thread_id', None)

        await update.message.reply_text(
            f"chat_id: {chat_id}\nuser_id: {user_id}" + (f"\nthread_id: {thread_id}" if thread_id is not None else "")
        )

        print(f"Chat ID: {chat_id} | User ID: {user_id} {f'| Thread ID: {thread_id}' if thread_id is not None else ''} | Message: {message_text}")
    else:  # Сообщение от канала
        message_text = update.channel_post.text

        print(f"Chat ID: {chat_id} | Message: {message_text}")


def main():
    """
    Настраивает и запускает Telegram-бота.

    Создает объект `Application`, добавляет обработчики для команды /start и текстовых сообщений,
    после чего запускает бота с использованием polling.
    """
    application = Application.builder().token(config.telegram_bot_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))

    application.run_polling()


if __name__ == "__main__":
    main()
