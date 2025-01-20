from googleapiclient.errors import HttpError


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
                    "video_id": video_id,
                    "author": top_comment['authorDisplayName'],
                    "text": top_comment['textDisplay'],
                    "publish_date": top_comment['publishedAt'],
                    "updated_date": top_comment.get('updatedAt'),
                    "reply_to": None
                })

                if 'replies' in item:
                    for reply in item['replies']['comments']:
                        reply_snippet = reply['snippet']
                        comments.append({
                            "video_id": video_id,
                            "author": reply_snippet['authorDisplayName'],
                            "text": reply_snippet['textDisplay'],
                            "publish_date": reply_snippet['publishedAt'],
                            "updated_date": reply_snippet.get('updatedAt'),
                            "reply_to": f"{video_id}_{top_comment['authorDisplayName']}_{top_comment['publishedAt']}"
                        })

            request = youtube_service.commentThreads().list_next(request, response)
        except HttpError as e:
            if e.resp.status in [403, 404]:
                break

            logger.error(f"Ошибка при получении комментариев для видео {video_id}: {e}")

            break
        except Exception as e:
            logger.error(f"Ошибка при обновлении комментариев видео {video_id}: {e}")

            break

    return comments
