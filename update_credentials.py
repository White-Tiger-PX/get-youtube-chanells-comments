import os
import time
import pickle
import signal
import random
import threading
import webbrowser

from google_auth_oauthlib.flow import InstalledAppFlow

import config

from open_url_with_chrome_profile import open_url_with_chrome_profile


def run_local_server(flow, port, logger):
    try:
        return flow.run_local_server(port=port, access_type='offline', open_browser=False)
    except Exception as err:
        logger.info(f"Ошибка при запуске локального сервера: {err}")

        raise


def stop_server_after_timeout(start_time, timeout, stop_event, logger):
    try:
        while time.time() - start_time < timeout:
            time.sleep(1)

            if stop_event and stop_event.is_set():
                return

        os.kill(os.getpid(), signal.SIGTERM)  # Завершаем процесс с помощью сигнала
    except Exception as e:
        logger.info(f"Ошибка при завершении сервера после тайм-аута: {e}")


def update_credentials(client_secret_path, token_path, timeout, logger):
    try:
        start_time = time.time()
        stop_event = threading.Event()

        port = random.randint(1024, 65535)

        flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, config.scopes)
        server_thread = threading.Thread(target=run_local_server, args=(flow, port, logger))
        server_thread.start()

        timer_thread = threading.Thread(target=stop_server_after_timeout, args=(start_time, timeout, stop_event, logger))
        timer_thread.daemon = True
        timer_thread.start()

        time.sleep(3)

        url = flow.authorization_url()[0]


        if config.use_specific_chrome_profile:
            open_url_with_chrome_profile(
                chrome_executable_path=config.chrome_executable_path,
                user_data_dir=config.user_data_dir,
                profile_directory=config.profile_directory,
                url=url,
                logger=logger
            )
        else:
            webbrowser.open(url)

        server_thread.join(timeout=timeout)

        if server_thread.is_alive():
            logger.warning("Время для аутентификации истекло.")

            return None

        credentials = flow.credentials

        with open(token_path, 'wb+') as token:
            pickle.dump(credentials, token)

        return credentials
    except Exception as err:
        logger.error(f"Ошибка в процессе обновления учетных данных: {err}")

        return None
    finally:
        stop_event.set()
        time.sleep(5)
