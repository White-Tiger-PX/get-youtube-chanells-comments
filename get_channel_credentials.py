import os
import sys
import pickle
import subprocess
from typing import Optional

from google.auth.transport.requests import Request
from google.auth.credentials import Credentials

from show_message_box import show_message_box


def load_credentials(token_path: str) -> Optional[object]:
    """
    Загружает учетные данные из файла токена, если он существует.

    Args:
        token_path (str): Путь к файлу, содержащему сериализованные учетные данные.

    Returns:
        object: Загруженные учетные данные (например, объект google.auth.credentials.Credentials),
                или None, если файл не существует.
    """
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token_file:
            return pickle.load(token_file)

    return None


def save_credentials(credentials: object, token_path: str) -> None:
    """
    Сохраняет учетные данные в файл токена.

    Args:
        credentials (object): Объект учетных данных для сохранения.
        token_path (str): Путь к файлу, куда будут сохранены учетные данные.
    """
    with open(token_path, 'wb') as token_file:
        pickle.dump(credentials, token_file)


def prompt_update_token(token_path: str) -> bool:
    """
    Выводит окно с запросом на обновление токена.

    Args:
        token_path (str): Путь к файлу токена, который требуется обновить.

    Returns:
        bool: True, если пользователь согласился на обновление токена,
              иначе False.
    """
    result = show_message_box(
        title="Обновление токена",
        message=f"Необходимо обновить токен {token_path}. Начать обновление?",
        text_button_true="Начать обновление токена"
    )

    return result == 1


def run_update_credentials_subprocess(client_secret_path: str, token_path: str, timeout: int, logger) -> Optional[object]:
    """
    Запускает процесс обновления учетных данных через subprocess.

    Функция инициирует процесс обновления, предварительно запросив подтверждение у пользователя.
    Если обновление прошло успешно, происходит повторная загрузка обновлённых учетных данных.

    Args:
        client_secret_path (str): Путь к файлу с секретом клиента (client_secret.json).
        token_path (str): Путь к файлу, где хранится токен доступа.
        timeout (int): Таймаут для сетевых запросов при обновлении токена.
        logger (logging.Logger): Логгер для записи информации и ошибок.

    Returns:
        object: Обновлённые учетные данные при успешном обновлении,
                или None, если обновление не было выполнено или завершилось с ошибкой.
    """
    if prompt_update_token(token_path) is False:
        return None

    subprocess_result = subprocess.run([
        sys.executable, '-m', 'update_credentials',
        client_secret_path, token_path, str(timeout)
    ], capture_output=True, text=True, check=False)

    if subprocess_result.returncode == 0:
        try:
            credentials = load_credentials(token_path)
            logger.info("Учетные данные %s обновлены.", token_path)

            return credentials
        except Exception as e:
            logger.error("Ошибка загрузки обновленных учетных данных %s: %s", token_path, e)
    else:
        logger.error("Ошибка при запуске обновления токена: %s", subprocess_result.stderr)

    return None


def refresh_existing_credentials(credentials: object, token_path: str, logger) -> object:
    """
    Пытается обновить истекшие учетные данные с использованием refresh_token.

    Если обновление проходит успешно, новые данные сохраняются в файле.
    Если обновление не удалось, функция возвращает исходный объект учетных данных без изменений.

    Args:
        credentials (object): Объект учетных данных, который необходимо обновить.
        token_path (str): Путь к файлу, где хранятся учетные данные.
        logger (logging.Logger): Логгер для записи информации и ошибок.

    Returns:
        object: Объект учетных данных после попытки обновления (None).
    """
    try:
        credentials.refresh(Request())
        save_credentials(credentials, token_path)

        logger.info("Токен %s успешно обновлен.", token_path)

        return credentials
    except Exception as err:
        if "invalid_grant" in str(err):
            logger.error("refresh_token аннулирован. Требуется переавторизация.")
        else:
            logger.error("Ошибка обновления токена: %s", err)

    return None


def get_channel_credentials(client_secret_path: str, token_path: str, timeout: int, main_logger) -> Optional[Credentials]:
    """
    Получает учетные данные канала, проверяя и обновляя токен доступа, если это необходимо.

    Сначала функция пытается загрузить учетные данные из указанного файла.
    Если учетные данные существуют и действительны, они возвращаются.
    Если токен истек, но имеется refresh_token, происходит попытка его обновления.
    В случае неудачи обновления через refresh_token или отсутствия учетных данных,
    инициируется процесс обновления через subprocess с подтверждением пользователя.

    Args:
        client_secret_path (str): Путь к файлу с секретом клиента (client_secret.json).
        token_path (str): Путь к файлу, где хранится токен доступа.
        timeout (int): Таймаут для сетевых запросов при обновлении токена.
        main_logger (logging.Logger): Логгер.

    Returns:
        object: Объект учетных данных канала (например, google.auth.credentials.Credentials),
                или None, если не удалось получить или обновить учетные данные.
    """
    logger = main_logger.getChild('get_channel_credentials')

    try:
        credentials = load_credentials(token_path)

        if credentials is not None and credentials.valid:
            return credentials

        if credentials and credentials.expired and credentials.refresh_token:
            refreshed = refresh_existing_credentials(credentials, token_path, logger)

            if refreshed:
                return refreshed

        logger.info("Обновление учетных данных %s.", token_path)

        # Если обновление через refresh_token не удалось — пробуем subprocess:
        return run_update_credentials_subprocess(client_secret_path, token_path, timeout, logger)
    except Exception as err:
        logger.error("Ошибка при получении токена %s: %s", token_path, err)

        show_message_box(
            title            = "Ошибка получения токена",
            message          = f"Не удалось получить токен: {str(err)}",
            text_button_true = "Начать обновление токена"
        )

    return None
