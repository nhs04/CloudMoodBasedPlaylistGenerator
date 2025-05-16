import boto3
import json
import re
import time

# AWS clients
comprehend = boto3.client('comprehend')
dynamodb = boto3.resource('dynamodb')
playlist_table = dynamodb.Table('MoodPlaylists')
user_data_table = dynamodb.Table('UserData')  # NEW table for saving user playlist history

def classify_mood(text, sentiment):
    text = text.lower()
    mood_patterns = {
        "Heartbroken": r"\bbroke up\b|\bheartbroken\b|\bsad\b|\blonely\b|\bloss\b|\bdepressed\b|\bcrying\b|\bdevastated\b",
        "Joyful": r"\bhappy\b|\bgreat day\b|\bjoyful\b|\bcheerful\b|\blaughing\b|\bgrateful\b|\bfeeling good\b|\bsuccess\b",
        "Excited": r"\bexcited\b|\btrip\b|\btravel\b|\bgraduating\b|\bcan’t wait\b|\bpumped\b|\bthrilled\b|\bsuper happy\b",
        "Stressed": r"\bstressed\b|\boverwhelmed\b|\btoo much work\b|\bpressure\b|\bdeadlines\b|\bexhausted\b|\bburned out\b",
        "Reflective": r"\bthinking\b|\breflect\b|\bcontemplating\b|\bdeep thoughts\b|\blife\b|\bmeaning\b|\bself\b|\bintrospect\b",
        "Anxious": r"\banxious\b|\bworry\b|\bnervous\b|\bscared\b|\bpanic\b|\bshaky\b|\buncertain\b",
        "Party Mode": r"\bparty\b|\bdancing\b|\bclubbing\b|\blit\b|\bdrunk\b|\bvibe\b|\brager\b|\bcelebration\b",
        "Nostalgic": r"\bnostalgic\b|\breminisce\b|\bsentimental\b|\bchildhood\b|\bmemories\b|\bold days\b|\btbt\b",
        "Chill Vibes": r"\bchill\b|\bcalm\b|\bunwind\b|\bpeaceful\b|\bserene\b|\bcozy\b|\bsunday\b|\braining\b",
        "Focused": r"\bfocus\b|\bworking\b|\bstudy\b|\bconcentrate\b|\bproductive\b|\bgrind\b|\bzone in\b",
    }

    for mood, pattern in mood_patterns.items():
        if re.search(pattern, text):
            return mood

    fallback = {
        "POSITIVE": "Joyful",
        "NEGATIVE": "Heartbroken",
        "NEUTRAL": "Undefined Vibes"
    }

    return fallback.get(sentiment, "Reflective")

def get_spotify_embed(url):
    try:
        playlist_id = url.split("playlist/")[1].split("?")[0]
        return f"https://open.spotify.com/embed/playlist/{playlist_id}"
    except:
        return ""

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        text = body.get('mood')
        user_id = body.get('userId')  # must be passed from frontend when logged in

        if not text:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "No input text provided"})
            }

        sentiment_response = comprehend.detect_sentiment(Text=text, LanguageCode='en')
        sentiment = sentiment_response['Sentiment']
        mood = classify_mood(text, sentiment)
        print(f"✅ Input: {text}")
        print(f"✅ Sentiment: {sentiment}")
        print(f"✅ Classified Mood: {mood}")

        mood_lower = mood.strip().lower()
        response = playlist_table.scan()
        items = response.get("Items", [])

        matched = next((item for item in items if item["mood"].strip().lower() == mood_lower), None)

        if matched:
            playlist = matched
        else:
            playlist = {
                "playlist_title": "No Mood. Just Music.",
                "description": "A mix of moods. When you're not sure what to feel 🎵",
                "url": "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
            }

        embed_url = get_spotify_embed(playlist["url"])

        # ❌ DO NOT SAVE inside analyze mood
        print(f"✅ Returning playlist result to frontend without saving.")


        return {
            "statusCode": 200,
            "body": json.dumps({
                "input": text,
                "sentiment": sentiment,
                "mood": mood,
                "playlist": {
                    "title": playlist["playlist_title"],
                    "description": playlist["description"],
                    "embed_url": embed_url
                }
            })
        }

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
