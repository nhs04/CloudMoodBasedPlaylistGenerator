import boto3
import json
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
table = dynamodb.Table('UserData')

SNS_TOPIC_ARN = 'arn:aws:sns:eu-west-1:438465165149:PlaylistSaved'

def normalize_url(url):
    if not url:
        return ""
    url = url.strip()
    if "/embed/playlist/" in url:
        url = url.replace("/embed/playlist/", "/playlist/")
    elif url.startswith("https://open.spotify.com/embed/playlist/"):
        url = url.replace("https://open.spotify.com/embed/playlist/", "https://open.spotify.com/playlist/")
    return url.lower().strip()

def convert_to_embed_url(url):
    """Convert Spotify playlist URL to embed version."""
    if "/playlist/" in url:
        playlist_id = url.split("/playlist/")[1].split("?")[0]
        return f"https://open.spotify.com/embed/playlist/{playlist_id}?utm_source=generator"
    return url

def lambda_handler(event, context):
    try:
        print("🔍 RAW EVENT:", event)

        body = event.get('body')
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "Invalid JSON body"})
                }
        elif not isinstance(body, dict):
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing or invalid body"})
            }

        user_id = body.get("userId")
        raw_url = body.get("playlistURL")
        normalized_url = normalize_url(raw_url)
        embed_url = convert_to_embed_url(normalized_url)  # ✅ FIX: store embed version

        title = body.get("playlistTitle", "").strip()
        description = body.get("playlistDescription", "").strip()
        mood = body.get("mood", "").strip()
        timestamp = body.get("timestamp")

        if not user_id or not embed_url or not title or not timestamp:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required fields"})
            }

        table.put_item(Item={
            "userId": user_id,
            "timestamp": timestamp,
            "mood": mood,
            "playlistTitle": title,
            "playlistURL": embed_url,
            "playlistDescription": description
        })

        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject='🎵 New Playlist Saved!',
            Message=(
                f"✅ A new playlist was saved!\n\n"
                f"User ID: {user_id}\n"
                f"Mood: {mood}\n"
                f"Title: {title}\n"
                f"URL: {embed_url}\n"
                f"Description: {description}"
            )
        )

        print("📨 SNS sent successfully!")
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Playlist saved!"})
        }

    except Exception as e:
        print("❌ ERROR:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
