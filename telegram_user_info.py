from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters
)

import config


async def start(update: Update, context):
    chat_id = update.effective_chat.id  # Получаем chat_id
    user_id = update.effective_user.id  # Получаем user_id
    message_text = update.message.text  # Получаем текст сообщения от пользователя

    await update.message.reply_text(f"You chat_id: {chat_id}\You user_id: {user_id}")

    print(f"Chat ID: {chat_id} | User ID: {user_id} | Message: {message_text}")


def main():
    application = Application.builder().token(config.telegram_bot_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))

    application.run_polling()


if __name__ == "__main__":
    main()
