import os
import json
from datetime import datetime, timedelta

import config


def convert_utc_to_local(created_at, logger):
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
