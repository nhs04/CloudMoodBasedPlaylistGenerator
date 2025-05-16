import json
import boto3
from boto3.dynamodb.conditions import Key, Attr

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        user_id = body['userId']
        playlist_url = body['playlistURL']

        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('UserData')

        # Query all items with that userId
        response = table.query(
            KeyConditionExpression=Key('userId').eq(user_id)
        )

        items = response.get("Items", [])
        deleted = False

        for item in items:
            if item["playlistURL"] == playlist_url:
                table.delete_item(
                    Key={
                        "userId": item["userId"],
                        "timestamp": item["timestamp"]
                    }
                )
                deleted = True

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": True
            },
            "body": json.dumps({"message": "Deleted" if deleted else "Not found"})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": True
            },
            "body": json.dumps({"error": str(e)})
        }
