import time
import requests


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

            for item in response['items']:
                top_comment = item['snippet']['topLevelComment']['snippet']

                comments.append({
                    "youtube_video_id": video_id,
                    "channel_id": item['snippet']['channelId'],

                    "comment_id": item['id'],
                    "author": top_comment['authorDisplayName'],
                    "author_channel_id": top_comment['authorChannelId']['value'],

                    "text": top_comment['textDisplay'],
                    "publish_date": top_comment['publishedAt'],
                    "updated_date": top_comment.get('updatedAt'),
                    "reply_to": None
                })

                if not 'replies' in item:
                    continue

                for reply in item['replies']['comments']:
                    comments.append({
                        "youtube_video_id": video_id,
                        "channel_id": reply['snippet']['channelId'],

                        "comment_id": reply['id'],
                        "author": reply['snippet']['authorDisplayName'],
                        "author_channel_id": reply['snippet']['authorChannelId']['value'],

                        "text": reply['snippet']['textDisplay'],
                        "publish_date": reply['snippet']['publishedAt'],
                        "updated_date": reply['snippet'].get('updatedAt'),
                        "reply_to": reply['snippet'].get('parentId')
                    })

            request = youtube_service.commentThreads().list_next(request, response)
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 401:
                break
            elif e.response.status_code == 403 and "commentsDisabled" in str(e):
                logger.warning(f"Комментарии отключены для видео {video_id}, пропускаем...")
                return []

            logger.error(f"Ошибка при получении комментариев для видео {video_id}: {e}")

            break
        except Exception as e:
            logger.error(f"Ошибка при обновлении комментариев видео {video_id}: {e}")

            break

    return comments
