from googleapiclient.errors import HttpError

import config

from utils import save_comment_data


def get_video_comments(youtube_service, video_id, logger):
    comments = []

    request = youtube_service.commentThreads().list(
        part="snippet,replies",
        videoId=video_id,
        maxResults=100,
        textFormat="plainText"
    )

    while request:
        try:
            response = request.execute()

            for item in response.get('items', []):
                try:
                    top_comment_data = item['snippet']['topLevelComment']

                    top_comment_data_to_db = {
                        "youtube_video_id": item['snippet']['videoId'],
                        "channel_id": item['snippet']['channelId'],

                        "comment_id": item['id'],
                        "author": top_comment_data['snippet']['authorDisplayName'],
                        "author_channel_id": top_comment_data['snippet']['authorChannelId']['value'],

                        "text": top_comment_data['snippet']['textDisplay'],
                        "publish_date": top_comment_data['snippet']['publishedAt'],
                        "updated_date": top_comment_data['snippet']['updatedAt'],
                        "reply_to": None
                    }

                    comments.append(top_comment_data_to_db)

                    if 'replies' in item:
                        for reply in item['replies']['comments']:
                            comments.append({
                                "youtube_video_id": reply['snippet']['videoId'],
                                "channel_id": reply['snippet']['channelId'],

                                "comment_id": reply['id'],
                                "author": reply['snippet']['authorDisplayName'],
                                "author_channel_id": reply['snippet']['authorChannelId']['value'],

                                "text": reply['snippet']['textDisplay'],
                                "publish_date": reply['snippet']['publishedAt'],
                                "updated_date": reply['snippet']['updatedAt'],
                                "reply_to": reply['snippet'].get('parentId')
                            })

                    if config.save_comments_data_to_json:
                        save_comment_data(item, logger)
                except KeyError as e:
                    logger.error(f"Отсутствует ключ {e} в комментарии: {item}")
                except Exception as e:
                    logger.error(f"Ошибка обработки комментария {item['id']}: {e}")

            request = youtube_service.commentThreads().list_next(request, response)
        except HttpError as e:
            error_message = str(e)

            if e.resp.status == 401:
                logger.warning("Ошибка 401: Недействительный API-ключ или истекший токен доступа.")

                break
            elif e.resp.status == 403 and "commentsDisabled" in error_message:
                logger.warning(f"Комментарии отключены для видео {video_id}, пропускаем...")

                break
            elif e.resp.status == 404:
                logger.error(f"Ошибка 404: Видео {video_id} не найдено.")

                break
            else:
                logger.error(f"Ошибка при получении комментариев для видео {video_id}: {error_message}")
        except Exception as e:
            logger.error(f"Ошибка при обновлении комментариев видео {video_id}: {e}")

    return comments
