
import os
import json

from datetime import datetime, timedelta

import config


def get_created_at_local(created_at, logger):
    try:
        # Преобразуем строку в datetime в формате UTC
        created_at = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")

        created_at_local = created_at + timedelta(hours=config.utc_offset_hours)

        return created_at_local
    except ValueError as err:
        logger.error(f"Ошибка преобразования даты: {err}")

        raise Exception("Ошибка в формате даты.")


def format_created_at_from_iso(created_at_iso, date_format, logger):
    """
    Преобразует дату в ISO формате в локальное время и форматирует в строку заданного формата.

    :param logger: Логгер для записи ошибок.
    :param created_at_iso: Дата в формате ISO (например, "2024-01-31T12:00:00Z").
    :param date_format: Формат для вывода даты (например, "%Y-%m-%d %H:%M:%S").
    :return: Строка с датой в заданном формате.
    """
    try:
        # Преобразование в объект datetime с учетом локального времени
        created_at_local = get_created_at_local(created_at_iso, logger)

        # Форматирование в строку по указанному формату
        return created_at_local.strftime(date_format)
    except Exception as err:
        logger.error(f"Ошибка обработки даты: {err}")

        raise ValueError(f"Ошибка обработки даты: {err}")


def load_json(file_path, default_type, logger):
    try:
        file_path = os.path.normpath(file_path)

        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        else:
            logger.warning("Файл %s не найден, возвращаем значение по умолчанию.", file_path)
    except Exception as err:
        logger.error("Ошибка при загрузке файла %s: %s", file_path, err)

    return default_type


def save_json(file_path, data, logger):
    try:
        file_path = os.path.normpath(file_path)

        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
    except Exception as err:
        logger.error("Ошибка при сохранении файла %s: %s", file_path, err)


def save_comment_data(comment_data, logger):
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
    except KeyError as e:
        logger.error(f"Отсутствует ожидаемый ключ в comment_data: {e}")
    except OSError as e:
        logger.error(f"Ошибка файловой системы: {e}")
    except Exception as e:
        logger.exception(f"Неожиданная ошибка в save_comment_data: {e}")
