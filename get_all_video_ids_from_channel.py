
import time
import googleapiclient.errors


def get_all_video_ids_from_channel(youtube_service, upload_playlist_id, logger):
    """
    Получает все идентификаторы видео из указанного плейлиста YouTube.

    :param youtube_service: Авторизованный клиент YouTube API.
    :param upload_playlist_id: Идентификатор плейлиста.
    :param logger: Логгер.
    :return: Список идентификаторов видео.
    """
    page_count = 0
    video_ids = []
    request = youtube_service.playlistItems().list(
        part="contentDetails",
        playlistId=upload_playlist_id,
        maxResults=50
    )

    while request:
        try:
            response = request.execute()
            video_ids.extend(
                item['contentDetails']['videoId'] for item in response['items']
            )
            page_count += 1
            logger.info(f"Страница {page_count}: {len(video_ids)} видео")

            request = youtube_service.playlistItems().list_next(request, response)
        except googleapiclient.errors.HttpError as e:
            if e.resp.status == 403 and 'quotaExceeded' in str(e):
                logger.error("Достигнут лимит квоты API YouTube. Попробуйте позже.")

                return None
            elif e.resp.status == 429:
                logger.warning("Слишком частые запросы к API YouTube. Замедляемся.")
                time.sleep(10)
            else:
                logger.error(f"Ошибка при получении данных: {e}")

                return None
        except Exception as e:
            logger.error(f"Неизвестная ошибка: {e}")

            return None

        # Пауза для предотвращения превышения лимитов запросов
        time.sleep(1)

    return video_ids
