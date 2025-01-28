import time
import asyncio
import sqlite3

from datetime import datetime, timedelta
from googleapiclient.discovery import build

import config

from set_logger import set_logger
from get_video_comments import get_video_comments
from telegram_notification import send_message_to_thread, send_message_to_chat
from get_channel_credentials import get_channel_credentials
from get_all_video_ids_from_channel import get_all_video_ids_from_channel


def get_created_at_local(created_at):
    try:
        # Преобразуем строку в datetime в формате UTC
        created_at = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")

        created_at_local = created_at + timedelta(hours=config.utc_offset_hours)

        return created_at_local
    except ValueError as err:
        logger.error(f"Ошибка преобразования даты: {err}")

        raise Exception("Ошибка в формате даты.")


def escape_markdown(text):
    """
    Экранирует зарезервированные символы Markdown V2.
    """
    if not text:
        return text

    reserved_chars = r'_*[]-()~`>#+-=|{}.!'

    return ''.join(f'\\{char}' if char in reserved_chars else char for char in text)


def format_created_at_from_iso(created_at_iso, date_format):
    """
    Преобразует дату в ISO формате в локальное время и форматирует в строку заданного формата.

    :param logger: Логгер для записи ошибок.
    :param created_at_iso: Дата в формате ISO (например, "2024-01-31T12:00:00Z").
    :param date_format: Формат для вывода даты (например, "%Y-%m-%d %H:%M:%S").
    :return: Строка с датой в заданном формате.
    """
    try:
        # Преобразование в объект datetime с учетом локального времени
        created_at_local = get_created_at_local(created_at_iso)

        # Форматирование в строку по указанному формату
        return created_at_local.strftime(date_format)
    except Exception as err:
        logger.error(f"Ошибка обработки даты: {err}")

        raise ValueError(f"Ошибка обработки даты: {err}")


def get_youtube_service(credentials):
    return build('youtube', 'v3', credentials=credentials)


def save_comments_to_db(database_path, comments, channel_name):
    if not comments:
        return

    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    insert_query = '''
        INSERT INTO comments (
            youtube_video_id,
            channel_name,
            text,
            author,
            publish_date,
            updated_date,
            reply_to,
            comment_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    '''

    select_query = '''
        SELECT 1 FROM comments WHERE comment_id = ? AND text = ?
    '''

    reply_query = '''
        SELECT text FROM comments WHERE comment_id = ?
    '''

    new_comments = []

    for comment in comments:
        video_id = comment['video_id']
        author = comment['author']
        text = comment['text']
        publish_date = comment['publish_date']
        updated_date = comment.get('updated_date')
        reply_to = comment.get('reply_to')
        comment_id = f"{video_id}_{author}_{publish_date}"

        cursor.execute(select_query, (comment_id, text))

        if cursor.fetchone():
            continue

        cursor.execute(insert_query, (video_id, channel_name, text, author, publish_date, updated_date, reply_to, comment_id))
        new_comments.append((author, text, publish_date, updated_date, reply_to, comment_id))

    conn.commit()
    conn.close()

    if not new_comments:
        return

    for author, text, publish_date, updated_date, reply_to, comment_id in new_comments:
        formatted_date = format_created_at_from_iso(publish_date, '%Y-%m-%d %H:%M:%S')

        video_url = f"https://www.com/watch?v={video_id}"
        channel_name_with_url = f"[{escape_markdown(channel_name)}]({video_url})"

        logger.info(f"Новый комментарий от {author}: {text}")

        is_updated = updated_date and updated_date != publish_date
        quoted_text = "\n".join(f"> {escape_markdown(line)}" for line in text.splitlines())

        if is_updated:
            quoted_text += "\n\n_\\(Комментарий изменён\\)_"

        if reply_to:
            conn = sqlite3.connect(database_path)
            cursor = conn.cursor()
            cursor.execute(reply_query, (reply_to,))
            reply_text_row = cursor.fetchone()
            conn.close()

            reply_text = (
                escape_markdown(reply_text_row[0])
                if reply_text_row
                else "_Комментарий не найден_"
            )

            reply_quoted_text = "\n".join(f"> {line}" for line in reply_text.splitlines())
            reply_note = f"\n\nОтвет на:\n{reply_quoted_text}"
        else:
            reply_note = ""

        telegram_message = (
            f"{channel_name_with_url}\n\n"
            f"*Автор:* {escape_markdown(author)}\n\n"
            f"{quoted_text}\n\n"
            f"*Дата:* {escape_markdown(formatted_date)}{reply_note}"
        )

        if config.user_id == config.chat_id:
            asyncio.run(
                send_message_to_chat(
                    message=telegram_message,
                    parse_mode='MarkdownV2',
                    main_logger=logger
                )
            )
        else:
            asyncio.run(
                send_message_to_thread(
                    message=telegram_message,
                    thread_id=config.thread_id,
                    parse_mode='MarkdownV2',
                    main_logger=logger
                )
            )
        time.sleep(5)


def get_user_name(youtube_service):
    """
    Получение имени пользователя через YouTube API.
    """
    try:
        response = youtube_service.channels().list(
            part="snippet",
            mine=True
        ).execute()

        if "items" in response and len(response["items"]) > 0:
            return response["items"][0]["snippet"]["title"]

        raise ValueError("Не удалось получить информацию о пользователе.")
    except Exception as e:
        logger.error(f"Ошибка при получении имени пользователя: {e}")

        raise

def get_channel_info(youtube_service):
    request = youtube_service.channels().list(
        part="id,snippet,contentDetails,statistics",
        mine=True
    )
    response = request.execute()

    if response['items']:
        return response['items'][0]

    return None


def main():
    for channel_data in config.chanells:
        try:
            token_path = channel_data["token_channel_path"]
            client_secret_path = channel_data["client_secret_path"]

            # Получение учетных данных для канала
            credentials = get_channel_credentials(
                client_secret_path=client_secret_path,
                token_path=token_path,
                user_name=None,  # user_name будет получен позже
                timeout=300,
                main_logger=logger
            )

            youtube_service = get_youtube_service(credentials)
            channel_info = get_channel_info(youtube_service)
            channel_name = channel_info['snippet']['title']
            upload_playlist_id = channel_info['contentDetails']['relatedPlaylists']['uploads']

            video_ids = get_all_video_ids_from_channel(
                youtube_service=youtube_service,
                upload_playlist_id=upload_playlist_id,
                logger=logger
            )

            for i, video_id in enumerate(video_ids):
                try:
                    print(f"Channel: {channel_name}, video: {video_id}...")
                    comments = get_video_comments(youtube_service, video_id, logger=logger)
                    save_comments_to_db(config.database_path, comments, channel_name)
                except Exception as e:
                    logger.error(f"Ошибка при обновлении комментариев для видео {video_id} от {channel_name}: {e}")

            logger.info(f"Обновлено {len(video_ids)} видео от {channel_name}")

        except Exception as e:
            logger.error(f"Ошибка обработки канала с токеном {token_path}: {e}")


if __name__ == "__main__":
    logger = set_logger(config.log_folder)

    main()
