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
from utils import format_created_at_from_iso


def escape_markdown(text):
    """
    Экранирует зарезервированные символы Markdown V2.
    """
    if not text:
        return text

    reserved_chars = r'_*[]-()~`>#+-=|{}.!'

    return ''.join(f'\\{char}' if char in reserved_chars else char for char in text)


def send_new_comments_to_telegram(new_comments, channel_name):
    for new_comment in new_comments:
        try:
            video_id = new_comment['youtube_video_id']
            author = new_comment['author']
            text = new_comment['text']
            publish_date = new_comment['publish_date']
            updated_date = new_comment['updated_date']
            reply_to = new_comment['reply_to']

            formatted_date = format_created_at_from_iso(publish_date, '%Y-%m-%d %H:%M:%S', logger)

            video_url = f"https://www.com/watch?v={video_id}"
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
                except Exception as db_err:
                    logger.error(f"Ошибка при получении текста родительского комментария: {db_err}")
                    reply_note = "\n\nОтвет на: _Ошибка при загрузке комментария_"

            telegram_message = (
                f"{channel_name_with_url}\n\n"
                f"*Автор:* {escape_markdown(author)}\n\n"
                f"{quoted_text}\n\n"
                f"*Дата:* {escape_markdown(formatted_date)}{reply_note}"
            )

            need_mention_user = True if config.user_id is not None else False

            try:
                if config.user_id == config.chat_id:
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

            except Exception as telegram_err:
                logger.error(f"Ошибка при отправке сообщения в Telegram: {telegram_err}")

        except KeyError as key_err:
            logger.error(f"Ошибка: отсутствует ключ в данных комментария: {key_err}")

        except Exception as e:
            logger.error(f"Ошибка обработки комментария: {e}")


def save_comments_to_db(database_path, comments, channel_name):
    if not comments:
        return []

    new_comments = []

    try:
        conn = sqlite3.connect(database_path)
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

                # Проверяем, есть ли уже такой комментарий с такой датой обновления
                cursor.execute('''
                    SELECT 1
                    FROM comments
                    WHERE comment_id = ? AND updated_date = ?
                ''', (comment_id, updated_date))

                if cursor.fetchone():  # Если комментарий уже есть, пропускаем
                    continue

                if reply_to:
                    logger.info(f"Новай запись с ответом на комментарий от {author}: {text}")
                else:
                    logger.info(f"Новая запись с комментарием от {author}: {text}")

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
                logger.error(f"Ошибка: отсутствует ключ в данных комментария: {key_err}")
            except Exception as comment_insert_err:
                logger.error(f"Ошибка обработки комментария {comment_id}: {comment_insert_err}")

        conn.commit()
    except sqlite3.Error as db_err:
        logger.error(f"Ошибка базы данных: {db_err}")
    except Exception as e:
        logger.error(f"Ошибка в функции save_comments_to_db: {e}")
    finally:
        conn.close()

    return new_comments


def main():
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

            logger.info(f"Началось обновление комментариев с канала [ {channel_name} ]")

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

                    logger.info(f"Обновление комментариев видео {video_label}")

                    comments = get_video_comments(youtube_service, video_id, logger=logger)
                    new_comments = save_comments_to_db(config.database_path, comments, channel_name)

                    if config.send_notification_on_telegram:
                        send_new_comments_to_telegram(new_comments, channel_name)
                except Exception as e:
                    logger.error(f"Ошибка при обновлении комментариев для {video_label}: {e}")
        except Exception as e:
            logger.error(f"Ошибка обработки канала с токеном {token_path}: {e}")


if __name__ == "__main__":
    logger = set_logger(config.log_folder)

    main()
