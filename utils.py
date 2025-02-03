import os
import json
from datetime import datetime, timedelta

import config


def get_created_at_local(created_at, logger):
    """
    Преобразует дату из UTC в локальное время.

    Args:
        created_at (str): Дата в формате UTC (например, "2024-02-01T12:00:00Z").
        logger (logging.Logger): Логгер.

    Returns:
        datetime: Дата в локальном времени.
    """
    try:
        created_at = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
        created_at_local = created_at + timedelta(hours=config.utc_offset_hours)

        return created_at_local
    except ValueError as err:
        logger.error("Ошибка преобразования даты: %s", err)
        raise ValueError("Ошибка в формате даты.") from err


def format_created_at_from_iso(created_at_iso, date_format, logger):
    """
    Преобразует дату из ISO-формата в локальное время и форматирует её.

    Args:
        created_at_iso (str): Дата в ISO-формате.
        date_format (str): Желаемый формат даты.
        logger (logging.Logger): Логгер.

    Returns:
        str: Отформатированная дата.
    """
    try:
        created_at_local = get_created_at_local(created_at_iso, logger)
        
        return created_at_local.strftime(date_format)
    except ValueError as err:
        logger.error("Ошибка обработки даты: %s", err)
        raise ValueError(f"Ошибка обработки даты: {err}") from err


def load_json(file_path, default_type, logger):
    """
    Загружает JSON-файл.

    Args:
        file_path (str): Путь к JSON-файлу.
        default_type (dict or list): Значение по умолчанию, если файл не найден или поврежден.
        logger (logging.Logger): Логгер.

    Returns:
        dict or list: Данные из JSON или значение по умолчанию.
    """
    try:
        file_path = os.path.normpath(file_path)

        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        else:
            logger.warning("Файл %s не найден, возвращаем значение по умолчанию.", file_path)
    except (json.JSONDecodeError, OSError) as err:
        logger.error("Ошибка при загрузке файла %s: %s", file_path, err)

    return default_type


def save_json(file_path, data, logger):
    """
    Сохраняет данные в JSON-файл.

    Args:
        file_path (str): Путь к JSON-файлу.
        data (dict or list): Данные для сохранения.
        logger (logging.Logger): Логгер.
    """
    try:
        file_path = os.path.normpath(file_path)

        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
    except OSError as err:
        logger.error("Ошибка при сохранении файла %s: %s", file_path, err)


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

        folder_path = os.path.join(
            config.path_to_comments_data_storage_dir,
            channel_id
        )

        os.makedirs(folder_path, exist_ok=True)

        video_metadata_save_path = os.path.join(
            folder_path,
            f"{channel_id} - {video_id} - {comment_id} - {updated_date}.json"
        )

        past_json_data = load_json(
            file_path=video_metadata_save_path,
            default_type={},
            logger=logger
        )

        past_comments = past_json_data.get('replies', {}).get('comments')
        current_comments = comment_data.get('replies', {}).get('comments')

        if past_json_data and past_comments == current_comments:
            return

        save_json(
            file_path=video_metadata_save_path,
            data=comment_data,
            logger=logger
        )
    except KeyError as err:
        logger.error("Отсутствует ожидаемый ключ в comment_data: %s", err)
    except OSError as err:
        logger.error("Ошибка файловой системы: %s", err)
    except Exception:
        logger.exception("Неожиданная ошибка в save_comment_data.")
