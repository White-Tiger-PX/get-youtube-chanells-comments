import sqlite3

import config

from set_logger import set_logger


def init_database(database_path: str, main_logger):
    """
    Инициализирует базу данных SQLite, создавая таблицу `comments`, если она не существует.

    Функция подключается к указанной базе данных, создаёт таблицу `comments` с нужными полями
    и закрывает соединение.

    Args:
        database_path (str): Путь к файлу базы данных SQLite.
        main_logger (logging.Logger): Логгер.
    """
    logger = main_logger.getChild('init_database')
    logger.info("Инициализация базы данных.")

    try:
        with sqlite3.connect(database_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    youtube_video_id TEXT NOT NULL,
                    channel_name TEXT NOT NULL,
                    channel_id TEXT NOT NULL,

                    comment_id TEXT NOT NULL,
                    author TEXT NOT NULL,
                    author_channel_id TEXT NOT NULL,

                    text TEXT NOT NULL,
                    publish_date TEXT,
                    updated_date TEXT,
                    reply_to TEXT
                )
            ''')

            conn.commit()

           logger.info("Инициализация базы данных завершена.")
    except Exception as err:
        logger.error("Ошибка при инициализации базы данных: %s", err)


if __name__ == "__main__":
    logger = set_logger(config.log_folder)

    init_database(database_path=config.database_path, main_logger=logger)
