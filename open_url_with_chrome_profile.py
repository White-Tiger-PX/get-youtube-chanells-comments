import subprocess


def open_url_with_chrome_profile(chrome_executable_path, user_data_dir, profile_directory, url, logger):
    """
    Открывает URL в Google Chrome с указанным профилем пользователя.

    Функция использует `subprocess.Popen` для запуска Chrome с заданными параметрами,
    включая путь к исполняемому файлу, директорию данных пользователя и конкретный профиль.

    Args:
        chrome_executable_path (str): Путь к исполняемому файлу Google Chrome.
        user_data_dir (str): Путь к директории данных пользователя Chrome.
        profile_directory (str): Название профиля Chrome, который будет использоваться.
        url (str): URL-адрес, который нужно открыть (может быть пустым).
        logger (logging.Logger): Логгер.

    Raises:
        FileNotFoundError: Если Chrome не найден по указанному пути.
        subprocess.CalledProcessError: Если при запуске Chrome произошла ошибка.
        Exception: Любая другая ошибка при запуске процесса.

    Returns:
        None
    """
    try:
        command = [
            chrome_executable_path,
            f'--user-data-dir={user_data_dir}',
            f'--profile-directory={profile_directory}'
        ]

        if url:
            command.append(url)

        subprocess.Popen(command)
    except FileNotFoundError as err:
        logger.error("Не удалось найти исполняемый файл Chrome: %s", err)

        raise
    except subprocess.CalledProcessError as err:
        logger.error("Ошибка при запуске Chrome: %s", err)

        raise
    except Exception as err:
        logger.error("Неизвестная ошибка при открытии URL: %s", err)

        raise
