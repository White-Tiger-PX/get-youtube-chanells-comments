from google.auth.transport.requests import AuthorizedSession
from googleapiclient.discovery import build


def get_youtube_service(credentials, timeout=15):
    """
    Создает сервисный объект YouTube API, используя переданные учетные данные.

    Args:
        credentials (google.auth.credentials.Credentials): Учётные данные пользователя.
        timeout (int, optional): Тайм-аут HTTP-сессии.

    Returns:
        googleapiclient.discovery.Resource: Сервис YouTube API для выполнения запросов.
    """
    http = AuthorizedSession(credentials, refresh_timeout=timeout)  # HTTP-сессия с авторизацией
    youtube_service = build('youtube', 'v3', credentials=credentials, cache_discovery=False)

    return youtube_service


def get_channel_info(youtube_service):
    """
    Получает информацию о канале, связанном с учетными данными пользователя.

    Args:
        youtube_service (googleapiclient.discovery.Resource): Авторизованный сервис YouTube API.

    Returns:
        dict or None: Информация о канале (id, snippet, contentDetails, statistics),
                      или None, если канал не найден.
    """
    request = youtube_service.channels().list(
        part="id,snippet,contentDetails,statistics",
        mine=True
    )
    response = request.execute()

    if response['items']:
        return response['items'][0]

    return None
