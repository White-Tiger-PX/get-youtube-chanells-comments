import os
import pickle

from google.auth.transport.requests import Request

from show_message_box import show_message_box
from update_credentials import update_credentials


def get_channel_credentials(client_secret_path, token_path, timeout, main_logger):
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

                logger.info(f"Токен {token_path} успешно обновлен.")
            except Exception as err:
                if "invalid_grant" in str(err):
                    logger.error("refresh_token аннулирован. Требуется переавторизация .")
                else:
                    logger.error(f"Ошибка обновления токена: {err}")

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

                logger.info(f"Учетные данные {token_path} обновлены.")

                with open(token_path, 'rb') as token:
                    credentials = pickle.load(token)
        else:
            logger.info(f"Обновление учетных данных {token_path}.")

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

            logger.info(f"Учетные данные {token_path} обновлены.")
    except Exception as err:
        logger.error(f"Ошибка при получении токена {token_path}: {err}")

        show_message_box(
            title="Ошибка получения токена",
            message=f"Не удалось получить токен: {str(err)}",
            text_button_true="Начать обновление токена"
        )

        return None

    return credentials
