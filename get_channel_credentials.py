import os
import pickle

from google.auth.transport.requests import Request

from show_message_box import show_message_box
from update_credentials import update_credentials


def get_channel_credentials(client_secret_path, token_path, timeout, main_logger):
    """
    Получает учетные данные канала, проверяя и обновляя токен доступа, если это необходимо.

    Сначала проверяется, существует ли токен. Если токен существует и действителен, он возвращается.
    Если токен истек, но имеется `refresh_token`, пытается обновить токен.
    Если обновление не удалось или токен отсутствует, уведомляет пользователя о необходимости обновления учетных данных и инициирует процесс обновления.

    Args:
        client_secret_path (str): Путь к файлу с секретом клиента (client_secret.json).
        token_path (str): Путь к файлу, где хранится токен доступа.
        timeout (int): Таймаут для сетевых запросов при обновлении токена.
        main_logger (logging.Logger): Логгер для записи информации о процессе.

    Returns:
        google.auth.credentials.Credentials: Объект учетных данных канала.
        None: Если не удалось получить или обновить учетные данные.
    """
    logger = main_logger.getChild('get_channel_credentials')
    token_path = os.path.normpath(token_path)
    credentials = None

    try:
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                credentials = pickle.load(token)

        if credentials is not None and credentials.valid:
            return credentials

        if credentials and credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())  # Попытаться обновить токен через refresh_token

                with open(token_path, 'wb') as token:
                    pickle.dump(credentials, token)

                logger.info("Токен %s успешно обновлен.", token_path)
            except Exception as err:
                if "invalid_grant" in str(err):
                    logger.error("refresh_token аннулирован. Требуется переавторизация.")
                else:
                    logger.error("Ошибка обновления токена: %s", err)

                result = show_message_box(
                    title="Обновление токена",
                    message=f"Необходимо обновить токен {token_path}. Начать обновление?",
                    text_button_true="Начать обновление токена"
                )

                if result != 1:
                    return None

                update_credentials(
                    client_secret_path=client_secret_path,
                    token_path=token_path,
                    timeout=timeout,
                    logger=logger
                )

                logger.info("Учетные данные %s обновлены.", token_path)

                with open(token_path, 'rb') as token:
                    credentials = pickle.load(token)
        else:
            logger.info("Обновление учетных данных %s.", token_path)

            result = show_message_box(
                title="Обновление токена",
                message=f"Необходимо обновить токен {token_path}. Начать обновление?",
                text_button_true="Начать обновление токена"
            )

            if result != 1:
                return None

            update_credentials(
                client_secret_path=client_secret_path,
                token_path=token_path,
                timeout=timeout,
                logger=logger
            )

            with open(token_path, 'rb+') as token:
                credentials = pickle.load(token)

            logger.info("Учетные данные %s обновлены.", token_path)
    except Exception as err:
        logger.error("Ошибка при получении токена %s: %s", token_path, err)

        show_message_box(
            title="Ошибка получения токена",
            message=f"Не удалось получить токен: {str(err)}",
            text_button_true="Начать обновление токена"
        )

        return None

    return credentials
