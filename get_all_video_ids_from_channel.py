import time
import googleapiclient.errors


def get_all_video_ids_from_channel(youtube_service, upload_playlist_id, channel_name, logger):
    """
    Получает все идентификаторы видео из указанного плейлиста YouTube.

    Args:
        youtube_service (googleapiclient.discovery.build): Авторизованный клиент YouTube API.
        upload_playlist_id (str): Идентификатор плейлиста.
        channel_name (str): Название канала.
        logger (logging.Logger): Логгер для записи логов.

    Returns:
        list: Список идентификаторов видео, если запрос успешен.
        None: Если возникла ошибка (например, превышение квоты или ошибка API).
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
            logger.info("Канал: %s | Страница: %d | Всего видео: %d", channel_name, page_count, len(video_ids))

            request = youtube_service.playlistItems().list_next(request, response)
        except googleapiclient.errors.HttpError as err:
            if err.resp.status == 403 and 'quotaExceeded' in str(err):
                logger.error("Достигнут лимит квоты API YouTube. Попробуйте позже.")

                return None
            elif err.resp.status == 429:
                logger.warning("Слишком частые запросы к API YouTube. Замедляемся.")
                time.sleep(10)
            else:
                logger.error("Ошибка при получении данных: %s", err)

                return None
        except Exception as err:
            logger.error("Неизвестная ошибка: %s", err)

            return None

        # Пауза для предотвращения превышения лимитов запросов
        time.sleep(1)

    return video_ids
