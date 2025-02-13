"""
Модуль для работы с файлами JSON.

Краткое описание функций:
- save_json: Сохраняет данные в формате JSON в файл.
- load_json: Загружает данные из JSON файла или возвращает значение по умолчанию.
"""
import os
import json


def save_json(file_path: str, data: dict, logger):
    """
    Сохраняет данные в формате JSON в файл.

    Args:
        file_path (str): Путь к файлу, в который нужно сохранить данные.
        data (dict): Данные, которые нужно сохранить в файл.
        logger (logging.Logger): Логгер.
    """
    try:
        file_path = os.path.normpath(file_path)

        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
    except Exception as err:
        logger.error("Ошибка при сохранении файла %s: %s", file_path, err)


def load_json(file_path: str, default_type: dict, logger) -> dict:
    """
    Загружает данные из JSON файла. Если файл не найден или произошла ошибка, возвращает значение по умолчанию.

    Args:
        file_path (str): Путь к файлу, из которого нужно загрузить данные.
        default_type (dict): Значение по умолчанию, которое будет возвращено, если файл не найден или произошла ошибка.
        logger (logging.Logger): Логгер.

    Returns:
        dict: Данные, загруженные из JSON файла, или значение по умолчанию в случае ошибки или отсутствия файла.
    """
    try:
        file_path = os.path.normpath(file_path)

        if not os.path.exists(file_path):
            logger.warning("Файл %s не найден, возвращаем значение по умолчанию.", file_path)

        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as err:
        logger.error("Ошибка при загрузке файла %s: %s", file_path, err)

    return default_type
