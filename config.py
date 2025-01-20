# Путь к папке для логов трансляций (измените на свой путь)
log_folder = "logs/get_youtube_chanells_comments"

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

# Идентификатор пользователя для Telegram
# Если у вас группа без подтем, то user_id будет совпадать с chat_id
user_id = "your_user_id_here"  # Замените на ваш уникальный идентификатор пользователя

# Идентификатор чата Telegram, может совпадать с user_id для групп без подтем
chat_id = "your_chat_id_here"  # Замените на ваш уникальный идентификатор чата

thread_id = 0 # Замените на нужный id темы

# Токен для Telegram бота (замените на свой)
telegram_bot_token = "your_telegram_bot_token_here"

# Чтобы получить user_id и chat_id, thread_id для вашего Telegram чата,
# используйте скрипт get_telegram_message_info.py

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
