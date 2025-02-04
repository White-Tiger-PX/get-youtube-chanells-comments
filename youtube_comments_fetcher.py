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
from utils import load_json, save_json, format_created_at_from_iso


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


def send_new_comments_to_telegram(new_comments, channel_name):
    """
    Отправляет новые комментарии в Telegram.

    Args:
        new_comments (list): Список новых комментариев.
        channel_name (str): Имя канала.
    """
    for new_comment in new_comments:
        try:
            video_id = new_comment['youtube_video_id']
            author = new_comment['author']
            text = new_comment['text']
            publish_date = new_comment['publish_date']
            updated_date = new_comment['updated_date']
            reply_to = new_comment['reply_to']

            formatted_date = format_created_at_from_iso(
                created_at_iso=publish_date,
                date_format='%Y-%m-%d %H:%M:%S',
                logger=logger
            )

            video_url = f"https://www.youtube.com/watch?v={video_id}"
            channel_name_with_url = f"[{escape_markdown(channel_name)}]({video_url})"

            is_updated = updated_date and updated_date != publish_date
            quoted_text = "\n".join(f"> {escape_markdown(line)}" for line in text.splitlines())

            if is_updated:
                quoted_text += "\n\n_\\(Комментарий изменён\\)_"

            reply_note = ""

            if reply_to:
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

                    reply_text = escape_markdown(reply_text_row[0] if reply_text_row else "_Комментарий не найден_")

                    reply_quoted_text = "\n".join(f"> {line}" for line in reply_text.splitlines())
                    reply_note = f"\n\nОтвет на:\n{reply_quoted_text}"
                except Exception as err:
                    logger.error("Ошибка при получении текста родительского комментария: %s", err)
                    reply_note = "\n\nОтвет на: _Ошибка при загрузке комментария_"

            telegram_message = (
                f"{channel_name_with_url}\n\n"
                f"*Автор:* {escape_markdown(author)}\n\n"
                f"{quoted_text}\n\n"
                f"*Дата:* {escape_markdown(formatted_date)}{reply_note}"
            )

            need_mention_user = True if config.user_id is not None else False

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


def save_comments_to_db(database_path, comments, channel_name):
    """
    Сохраняет новые комментарии в базу данных.

    Args:
        database_path (str): Путь к базе данных.
        comments (list): Список комментариев.
        channel_name (str): Имя канала.

    Returns:
        list: Список новых комментариев, успешно сохранённых в базу данных.
    """
    if not comments:
        return []

    new_comments = []

    try:
        with sqlite3.connect(database_path) as conn:
            cursor = conn.cursor()

            for comment in comments:
                try:
                    video_id = comment['youtube_video_id']
                    channel_id = comment['channel_id']
                    comment_id = comment['comment_id']
                    author = comment['author']
                    author_channel_id = comment['author_channel_id']
                    text = comment['text']
                    publish_date = comment['publish_date']
                    updated_date = comment['updated_date']
                    reply_to = comment['reply_to']

                    if comment_exists(cursor=cursor, comment_id=comment_id, updated_date=updated_date):
                        continue

                    if reply_to:
                        logger.info("Новая запись с ответом на комментарий от %s: %s", author, text)
                    else:
                        logger.info("Новая запись с комментарием от %s: %s", author, text)

                    cursor.execute('''
                        INSERT INTO comments (
                            youtube_video_id,
                            channel_name,
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
                        video_id,
                        channel_name,
                        channel_id,
                        comment_id,
                        author,
                        author_channel_id,
                        text,
                        publish_date,
                        updated_date,
                        reply_to
                    ))

                    new_comments.append(comment)
                except KeyError as key_err:
                    logger.error("Ошибка: отсутствует ключ в данных комментария: %s", key_err)
                except Exception as err:
                    logger.error("Ошибка обработки комментария %s: %s", comment_id, err)
    except sqlite3.Error as err:
        logger.error("Ошибка базы данных: %s", err)
    except Exception as err:
        logger.error("Ошибка в функции save_comments_to_db: %s", err)

    return new_comments


def comments_have_changed(past_data, current_data):
    past_comments = past_data.get('replies', {}).get('comments')
    current_comments = current_data.get('replies', {}).get('comments')

    return past_comments != current_comments


def generate_save_path(channel_id, video_id, comment_id, updated_date):
    folder_path = os.path.join(config.path_to_comments_data_storage_dir, channel_id)

    os.makedirs(folder_path, exist_ok=True)

    return os.path.join(folder_path, f"{channel_id} - {video_id} - {comment_id} - {updated_date}.json")


def save_comment_data(comment_data, logger):
    """
    Сохраняет комментарий в JSON-файл.

    Args:
        comment_data (dict): Данные комментария.
        logger (logging.Logger): Логгер.
    """
    try:
        top_level_comment_data = comment_data['snippet']['topLevelComment']

        channel_id = comment_data['snippet']['channelId']
        video_id = comment_data['snippet']['videoId']
        comment_id = comment_data['id']

        updated_date = format_created_at_from_iso(
            created_at_iso=top_level_comment_data['snippet']['updatedAt'],
            date_format="%Y-%m-%d %H-%M-%S",
            logger=logger
        )


        save_path = generate_save_path(channel_id, video_id, comment_id, updated_date)

        past_json_data = load_json(
            file_path=save_path,
            default_type={},
            logger=logger
        )

        if past_json_data and not comments_have_changed(past_json_data, comment_data):
            return

        save_json(
            file_path=save_path,
            data=comment_data,
            logger=logger
        )
    except KeyError as err:
        logger.error("Отсутствует ожидаемый ключ в comment_data: %s", err)
    except OSError as err:
        logger.error("Ошибка файловой системы: %s", err)
    except Exception:
        logger.exception("Неожиданная ошибка в save_comment_data.")


def format_comments(item):
    comments = []

    if config.save_comments_data_to_json:
        save_comment_data(item, logger)

    top_comment_data = item['snippet']['topLevelComment']

    top_comment_data_to_db = {
        "youtube_video_id": item['snippet']['videoId'],
        "channel_id": item['snippet']['channelId'],
        "comment_id": item['id'],
        "author": top_comment_data['snippet']['authorDisplayName'],
        "author_channel_id": top_comment_data['snippet']['authorChannelId']['value'],
        "text": top_comment_data['snippet']['textDisplay'],
        "publish_date": top_comment_data['snippet']['publishedAt'],
        "updated_date": top_comment_data['snippet']['updatedAt'],
        "reply_to": None
    }

    comments.append(top_comment_data_to_db)

    if 'replies' in item:
        for reply in item['replies']['comments']:
            comments.append({
                "youtube_video_id": reply['snippet']['videoId'],
                "channel_id": reply['snippet']['channelId'],
                "comment_id": reply['id'],
                "author": reply['snippet']['authorDisplayName'],
                "author_channel_id": reply['snippet']['authorChannelId']['value'],
                "text": reply['snippet']['textDisplay'],
                "publish_date": reply['snippet']['publishedAt'],
                "updated_date": reply['snippet']['updatedAt'],
                "reply_to": reply['snippet'].get('parentId')
            })

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

            youtube_service = get_youtube_service(credentials)
            channel_info = get_channel_info(youtube_service)
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

                    comments_data = get_video_comments(youtube_service, video_id, logger=logger)

                    if config.save_comments_data_to_json:
                        for comment_data in comments_data:
                            save_comment_data(comment_data, logger)

                    comments = format_comments(comment_data)
                    new_comments = save_comments_to_db(config.database_path, comments, channel_name)

                    if config.send_notification_on_telegram:
                        send_new_comments_to_telegram(new_comments, channel_name)
                except Exception as err:
                    logger.error("Ошибка при обновлении комментариев для %s: %s", video_label, err)

            logger.info("Завершено обновление комментариев с канала [ %s ]", channel_name)
        except Exception as err:
            logger.error("Ошибка обработки канала с токеном %s: %s", token_path, err)


if __name__ == "__main__":
    logger = set_logger(config.log_folder)

    main()
