import os
import time
import asyncio
import sqlite3

import config

from set_logger import set_logger
from init_database import init_database
from get_video_comments import get_video_comments
from get_channel_credentials import get_channel_credentials
from get_all_video_ids_from_channel import get_all_video_ids_from_channel
from telegram_notification import send_message_to_chat, send_message_to_group
from utils_youtube import get_channel_info, get_youtube_service
from utils import load_json, save_json, convert_utc_to_local


def escape_markdown(text):
    """
    Экранирует зарезервированные символы Markdown V2.

    Args:
        text (str): Текст, который нужно экранировать.

    Returns:
        str: Экранированный текст.
    """
    if not text:
        return text

    reserved_chars = r'_*[]-()~`>#+-=|{}.!'

    return ''.join(f'\\{char}' if char in reserved_chars else char for char in text)


def get_parent_comment_text(reply_to):
    """
    Получает текст родительского комментария.

    Args:
        reply_to (str): ID родительского комментария.

    Returns:
        str: Текст родительского комментария, отформатированный для Telegram.
    """
    try:
        conn = sqlite3.connect(config.database_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT text
            FROM comments
            WHERE comment_id = ?
        ''', (reply_to,))

        reply_text_row = cursor.fetchone()
        conn.close()

        reply_text = escape_markdown(text=reply_text_row[0]) if reply_text_row else "_Комментарий не найден_"
        reply_quoted_text = "\n".join(f"> {line}" for line in reply_text.splitlines())

        return f"\n\nОтвет на:\n{reply_quoted_text}"
    except Exception as err:
        logger.error("Ошибка при получении текста родительского комментария: %s", err)

        return "\n\nОтвет на: _Ошибка при загрузке комментария_"


def format_comment_for_telegram(new_comment, channel_name):
    """
    Форматирует текст комментария для отправки в Telegram.

    Args:
        new_comment (dict): Данные комментария.
        channel_name (str): Название канала.

    Returns:
        str: Отформатированное сообщение.
    """
    video_id     = new_comment['snippet']['videoId']
    author       = new_comment['snippet']['authorDisplayName']
    text         = new_comment['snippet']['textDisplay']
    publish_date = new_comment['snippet']['publishedAt']
    updated_date = new_comment['snippet']['updatedAt']
    reply_to     = new_comment['snippet'].get('parentId', None)

    publish_date_local = convert_utc_to_local(utc_time=publish_date, logger=logger)
    formatted_publish_date = publish_date_local.strftime('%Y-%m-%d %H:%M:%S')

    video_url = f"https://www.youtube.com/watch?v={video_id}"
    channel_name_with_url = f"[{escape_markdown(text=channel_name)}]({video_url})"

    is_updated = updated_date and updated_date != publish_date
    quoted_text = "\n".join(f"> {escape_markdown(text=line)}" for line in text.splitlines())

    if is_updated:
        quoted_text += "\n\n_\\(Комментарий изменён\\)_"

    reply_note = get_parent_comment_text(reply_to) if reply_to else ""

    return (
        f"{channel_name_with_url}\n\n"
        f"*Автор:* {escape_markdown(text=author)}\n\n"
        f"{quoted_text}\n\n"
        f"*Дата:* {escape_markdown(text=formatted_publish_date)}{reply_note}"
    )


def send_comment_to_telegram(new_comment, channel_name):
    """
    Отправляет комментарий в Telegram.

    Args:
        new_comment (dict): Данные комментария.
        channel_name (str): Название канала.
    """
    try:
        telegram_message = format_comment_for_telegram(new_comment, channel_name)
        need_mention_user = config.user_id is not None

        try:
            if config.user_id and config.user_id == config.chat_id:
                asyncio.run(
                    send_message_to_chat(
                        message=telegram_message,
                        parse_mode='MarkdownV2',
                        mention_user=need_mention_user,
                        main_logger=logger
                    )
                )
            else:
                asyncio.run(
                    send_message_to_group(
                        message=telegram_message,
                        thread_id=config.thread_id,
                        mention_user=need_mention_user,
                        parse_mode='MarkdownV2',
                        main_logger=logger
                    )
                )

            time.sleep(5)
        except Exception as err:
            logger.error("Ошибка при отправке сообщения в Telegram: %s", err)
    except KeyError as key_err:
        logger.error("Ошибка: отсутствует ключ в данных комментария: %s", key_err)
    except Exception as err:
        logger.error("Ошибка обработки комментария: %s", err)


def comment_exists(cursor, comment_id, updated_date):
    """
    Проверяет, существует ли комментарий в базе данных.

    Args:
        cursor (sqlite3.Cursor): Курсор базы данных.
        comment_id (str): Идентификатор комментария.
        updated_date (str): Дата обновления комментария.

    Returns:
        bool: True, если комментарий существует, иначе False.
    """
    cursor.execute('''
        SELECT 1
        FROM comments
        WHERE comment_id = ? AND updated_date = ?
    ''', (comment_id, updated_date))

    return cursor.fetchone() is not None


def insert_comment(cursor, comment_data, channel_name):
    """
    Вставляет новый комментарий в базу данных.

    Args:
        cursor (sqlite3.Cursor): Курсор базы данных.
        comment_data (dict): Данные комментария.
        channel_name (str): Имя канала.
    """
    cursor.execute('''
        INSERT INTO comments (
            channel_name,
            youtube_video_id,
            channel_id,
            comment_id,
            author,
            author_channel_id,
            text,
            publish_date,
            updated_date,
            reply_to
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        channel_name,
        comment_data['snippet']['videoId'],
        comment_data['snippet']['channelId'],
        comment_data['id'],
        comment_data['snippet']['authorDisplayName'],
        comment_data['snippet']['authorChannelId']['value'],
        comment_data['snippet']['textDisplay'],
        comment_data['snippet']['publishedAt'],
        comment_data['snippet']['updatedAt'],
        comment_data['snippet'].get('parentId', None)
    ))


def save_comments_to_db(database_path, items, channel_name):
    """
    Сохраняет новые комментарии и ответы в базу данных.

    Args:
        database_path (str): Путь к базе данных.
        items (list): Список комментариев (топовых и ответов).
        channel_name (str): Имя канала.

    Returns:
        list: Список новых комментариев и ответов, успешно сохранённых в базу данных.
    """
    if not items:
        return []

    new_comments = []

    try:
        with sqlite3.connect(database_path) as conn:
            cursor = conn.cursor()

            for comment_data in items:
                if not comment_data:
                    continue

                updated_date = comment_data['snippet']['updatedAt']
                comment_id   = comment_data['id']
                author       = comment_data['snippet']['authorDisplayName']
                text         = comment_data['snippet']['textDisplay']

                if comment_exists(cursor=cursor, comment_id=comment_id, updated_date=updated_date):
                    continue

                insert_comment(cursor=cursor, comment_data=comment_data, channel_name=channel_name)

                new_comments.append(comment_data)
                logger.info("Новая запись с комментарием от %s: %s", author, text)
    except sqlite3.Error as err:
        logger.error("Ошибка базы данных: %s", err)
    except Exception as err:
        logger.error("Ошибка в функции save_comments_to_db: %s", err)

    return new_comments


def generate_save_path(channel_id, video_id, comment_id, updated_date):
    """
    Генерирует путь для сохранения JSON-файла с данными комментария.

    Создает директорию для хранения данных, если её не существует, и формирует имя файла,
    включающее идентификаторы канала, видео, комментария и дату обновления.

    Args:
        channel_id (str): Идентификатор канала.
        video_id (str): Идентификатор видео.
        comment_id (str): Идентификатор комментария.
        updated_date (str): Отформатированная дата обновления комментария.

    Returns:
        str: Полный путь к файлу для сохранения данных комментария.
    """
    folder_path = os.path.join(config.path_to_comments_data_storage_dir, channel_id)

    os.makedirs(folder_path, exist_ok=True)

    return os.path.join(folder_path, f"{channel_id} - {video_id} - {comment_id} - {updated_date}.json")


def comments_have_changed(past_data, current_data):
    """
    Сравнивает данные комментариев из двух источников и определяет, изменились ли ответы.

    Функция извлекает список ответов (если они имеются) из прошлых и текущих данных и сравнивает их.

    Args:
        past_data (dict): Ранее сохранённые данные комментария.
        current_data (dict): Текущие данные комментария.

    Returns:
        bool: True, если данные ответов отличаются, иначе False.
    """
    past_comments = past_data.get('replies', {}).get('comments')
    current_comments = current_data.get('replies', {}).get('comments')

    return past_comments != current_comments


def save_comment_data_to_json(comment_data):
    """
    Сохраняет данные комментария в JSON-файл.

    Функция извлекает необходимую информацию из словаря комментария, формирует путь для сохранения файла,
    загружает предыдущие данные (если они существуют) и сравнивает их с текущими данными. Если данные изменились,
    производится сохранение обновленных данных в JSON-файл.

    Args:
        comment_data (dict): Словарь с данными комментария, полученными из API или другого источника.

    Raises:
        KeyError: Если ожидаемый ключ отсутствует в comment_data.
        OSError: Если возникает ошибка при работе с файловой системой.
        Exception: При возникновении непредвиденной ошибки.
    """
    try:
        top_level_comment_data = comment_data['snippet']['topLevelComment']
        updated_date           = top_level_comment_data['snippet']['updatedAt']
        channel_id             = comment_data['snippet']['channelId']
        video_id               = comment_data['snippet']['videoId']
        comment_id             = comment_data['id']

        updated_date_local = convert_utc_to_local(utc_time=updated_date, logger=logger)
        formatted_updated_date = updated_date_local.strftime('%Y-%m-%d %H-%M-%S')

        save_path = generate_save_path(
            channel_id=channel_id,
            video_id=video_id,
            comment_id=comment_id,
            updated_date=formatted_updated_date
        )
        past_json_data = load_json(file_path=save_path, default_type={}, logger=logger)

        if past_json_data and not comments_have_changed(past_data=past_json_data, current_data=comment_data):
            return

        save_json(file_path=save_path, data=comment_data, logger=logger)
    except KeyError as err:
        logger.error("Отсутствует ожидаемый ключ в comment_data: %s", err)
    except OSError as err:
        logger.error("Ошибка файловой системы: %s", err)
    except Exception:
        logger.exception("Неожиданная ошибка в save_comment_data_to_json.")


def extract_comments_with_replies(comments_data):
    """
    Извлекает комментарии и их ответы из предоставленных данных.

    Функция проходит по списку комментариев, извлекает верхнеуровневые комментарии и, если имеются,
    добавляет ответы к каждому из них в результирующий список.

    Args:
        comments_data (list): Список словарей с данными комментариев, полученными из API или другого источника.

    Returns:
        list: Список словарей, каждый из которых представляет либо топовый комментарий, либо ответ.
    """
    comments = []

    for comment_data in comments_data:
        try:
            top_comment_data = comment_data['snippet']['topLevelComment']
            comments.append(top_comment_data)

            if 'replies' in comment_data:
                for reply in comment_data['replies']['comments']:
                    comments.append(reply)
        except KeyError as err:
            logger.error("Отсутствует ключ %s в комментарии: %s", err, comment_data)
        except Exception as err:
            logger.error("Ошибка обработки комментария %s: %s", comment_data.get('id', 'неизвестный'), err)

    return comments


def main():
    """
    Главная функция для запуска процесса получения комментариев с каналов.
    """
    logger.info("Программа для получения комментариев с каналов запущена!")

    init_database(
        database_path=config.database_path,
        main_logger=logger
    )

    for channel_data in config.channels:
        try:
            token_path = channel_data["token_channel_path"]
            client_secret_path = channel_data["client_secret_path"]

            credentials = get_channel_credentials(
                client_secret_path=client_secret_path,
                token_path=token_path,
                timeout=300,
                main_logger=logger
            )

            youtube_service = get_youtube_service(credentials=credentials)
            channel_info = get_channel_info(youtube_service=youtube_service)
            channel_name = channel_info['snippet']['title']
            upload_playlist_id = channel_info['contentDetails']['relatedPlaylists']['uploads']

            logger.info("Началось обновление комментариев с канала [ %s ]", channel_name)

            video_ids = get_all_video_ids_from_channel(
                youtube_service=youtube_service,
                upload_playlist_id=upload_playlist_id,
                channel_name=channel_name,
                logger=logger
            )

            count_videos = len(video_ids)

            for i, video_id in enumerate(video_ids):
                try:
                    video_label = f"[ {channel_name} | {video_id} | {i+1}/{count_videos} ]"

                    logger.info("Обновление комментариев видео %s", video_label)

                    comments_data = get_video_comments(
                        youtube_service=youtube_service,
                        video_id=video_id,
                        logger=logger
                    )

                    # Сначала сохраняем комментарии в json
                    # проверяя, что нет изменения относительно локальных файлов
                    if config.save_comments_data_to_json:
                        for comment_data in comments_data:
                            save_comment_data_to_json(comment_data=comment_data)

                    # Добавляем новые записи в базу данных
                    comments_to_db = extract_comments_with_replies(comments_data=comments_data)
                    new_comments = save_comments_to_db(
                        database_path=config.database_path,
                        items=comments_to_db,
                        channel_name=channel_name
                    )

                    # Отправляем комментарии после их сохранения
                    if config.send_notification_on_telegram:
                        for new_comment in new_comments:
                            send_comment_to_telegram(new_comment=new_comment, channel_name=channel_name)
                except Exception as err:
                    logger.error("Ошибка при обновлении комментариев для %s: %s", video_label, err)

            logger.info("Завершено обновление комментариев с канала [ %s ]", channel_name)
        except Exception as err:
            logger.error("Ошибка обработки канала с токеном %s: %s", token_path, err)


if __name__ == "__main__":
    logger = set_logger(config.log_folder)

    main()
