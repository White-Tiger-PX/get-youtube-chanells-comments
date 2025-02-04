from googleapiclient.errors import HttpError


def get_video_comments(youtube_service, video_id, logger):
    """
    Получает комментарии к видео с YouTube, включая ответы на них.

    Функция делает запрос к YouTube API, получает комментарии и ответы на них.

    Args:
        youtube_service (googleapiclient.discovery.Resource): Авторизованный клиент YouTube API.
        video_id (str): Идентификатор видео, для которого нужно получить комментарии.
        logger (logging.Logger): Логгер.

    Returns:
        list: Список всех комментариев (items) и ответов.
    """
    items = []

    request = youtube_service.commentThreads().list(
        part="snippet,replies",
        videoId=video_id,
        maxResults=100,
        textFormat="plainText"
    )

    while request:
        try:
            response = request.execute()

            items.extend(response.get('items', []))  # Добавляем все комментарии и ответы

            # Переход к следующей странице, если она есть
            request = youtube_service.commentThreads().list_next(request, response)
        except HttpError as err:
            error_message = str(err)

            if err.resp.status == 401:
                logger.warning("Ошибка 401: Недействительный API-ключ или истекший токен доступа.")

                break
            elif err.resp.status == 403 and "commentsDisabled" in error_message:
                logger.warning("Комментарии отключены для видео %s, пропускаем...", video_id)

                break
            elif err.resp.status == 404:
                logger.error("Ошибка 404: Видео %s не найдено.", video_id)

                break
            else:
                logger.error("Ошибка при получении комментариев для видео %s: %s", video_id, error_message)
        except Exception as err:
            logger.error("Ошибка при обновлении комментариев видео %s: %s", video_id, err)

    return items
