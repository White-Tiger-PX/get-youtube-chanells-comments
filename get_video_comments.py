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
                except KeyError as err:
                    logger.error("Отсутствует ключ %s в комментарии: %s", err, item)
                except Exception as err:
                    logger.error("Ошибка обработки комментария %s: %s", item['id'], err)

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

    return comments
