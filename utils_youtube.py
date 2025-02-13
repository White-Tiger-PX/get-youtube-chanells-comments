from googleapiclient.discovery import build


def get_youtube_service(credentials):
    """
    Создает объект YouTube API, используя переданные учетные данные.

    Args:
        credentials (google.auth.credentials.Credentials): Учётные данные пользователя.

    Returns:
        googleapiclient.discovery.Resource: Учётные данные YouTube API для выполнения запросов.
    """
    youtube_service = build('youtube', 'v3', credentials=credentials, cache_discovery=False)

    return youtube_service


def get_channel_info(youtube_service):
    """
    Получает информацию о канале, связанном с учетными данными пользователя.

    Args:
        youtube_service (googleapiclient.discovery.Resource): Авторизованный сервис YouTube API.

    Returns:
        dict: Информация о канале (id, snippet, contentDetails, statistics),
              или пустой словарь, если канал не найден.
    """
    request = youtube_service.channels().list(
        part="id,snippet,contentDetails,statistics",
        mine=True
    )
    response = request.execute()

    if response.get('items', None):
        return response['items'][0]

    return {}
