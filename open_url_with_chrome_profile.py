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
        logger.error("Не удалось найти исполняемый файл Chrome: %s", err)

        raise
    except subprocess.CalledProcessError as err:
        logger.error("Ошибка при запуске Chrome: %s", err)

        raise
    except Exception as err:
        logger.error("Неизвестная ошибка при открытии URL: %s", err)

        raise
