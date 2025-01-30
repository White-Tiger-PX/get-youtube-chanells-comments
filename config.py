# Путь к папке для логов трансляций (измените на свой путь)
log_folder = "logs/youtube_comments_fetcher"

# Время смещения от UTC в часах
utc_offset_hours = 0

# Путь к базе данных (измените на свой путь)
database_path = "comments.db"

# Список разрешений для работы с YouTube API
scopes = [
    "https://www.googleapis.com/auth/youtube.upload",    # Для загрузки видео
    "https://www.googleapis.com/auth/youtube.readonly",  # Для получения информации о видео
    "https://www.googleapis.com/auth/youtube.force-ssl"  # Для авторизации
]

# Использование конкретного профиля Chrome
use_specific_chrome_profile = False

# Путь к данным профиля Chrome
user_data_dir = ""
profile_directory = "Profiles - "
chrome_executable_path = "C:/Program Files/Google/Chrome/Application/chrome.exe"

# Отправлять ли комментарии в Telegram
send_notification_on_telegram = False

# Чтобы получить user_id и chat_id, thread_id для вашего Telegram чата,
# используйте скрипт get_telegram_message_info.py

# Идентификатор чата Telegram, может совпадать с user_id для групп без подтем
# ID группы начинается с -100
chat_id = "your_chat_id_here"

# Уникальный идентификатор пользователя
# если хотите, чтобы бот упоминал вас в сообщениях (точка в конце)
user_id = None

# ID темы в Telegram, в которую необходимо отправить сообщение
# Главная тема имеет id = 0
# id тем совпадают с номером сообщений, в которых Telegram объявляет создание темы
thread_id = None

# Токен для Telegram бота (замените на свой)
telegram_bot_token = "your_telegram_bot_token_here"

# Параметр, указывающий, нужно ли сохранять данные комментариев в файлах json
save_comments_data_to_json = False

# Путь к папке для сохранения данных комментариев в файлах json
path_to_comments_data_storage_dir = "comments_data"

# Список каналов для работы с YouTube API
channels = [
    {
        "token_channel_path": "token_channel_1.pickle",
        "client_secret_path": "client_secret_1.json"
    },
    {
        "token_channel_path": "token_channel_2.pickle",
        "client_secret_path": "client_secret_2.json"
    }
]
