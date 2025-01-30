from google.auth.transport.requests import AuthorizedSession
from googleapiclient.discovery import build


def get_youtube_service(credentials, timeout=15):
    http = AuthorizedSession(credentials)
    youtube_service = build('youtube', 'v3', credentials=credentials, cache_discovery=False)

    return youtube_service


def get_channel_info(youtube_service):
    request = youtube_service.channels().list(
        part="id,snippet,contentDetails,statistics",
        mine=True
    )
    response = request.execute()

    if response['items']:
        return response['items'][0]

    return None
