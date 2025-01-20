import subprocess


def open_url_with_chrome_profile(chrome_executable_path, user_data_dir, profile_directory, url, logger):
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
        logger.error(f"Не удалось найти исполняемый файл Chrome: {err}")

        raise Exception(f'Исполняемый файл Chrome не найден: {chrome_executable_path}') from err
    except subprocess.CalledProcessError as err:
        logger.error(f"Ошибка при запуске Chrome: {err}")

        raise Exception(f"Ошибка выполнения команды: {command}") from err
    except Exception as err:
        logger.error(f"Неизвестная ошибка при открытии URL: {err}")

        raise err from err
