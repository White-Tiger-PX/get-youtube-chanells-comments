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
