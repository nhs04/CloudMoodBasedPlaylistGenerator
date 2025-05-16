import json
import boto3
from boto3.dynamodb.conditions import Key

def lambda_handler(event, context):
    print("EVENT:", event)

    try:
        # Parse the body and extract userId
        body = event.get('body')
        if body:
            body = json.loads(body)
            user_id = body.get('userId')
        else:
            # Fallback to queryStringParameters (if sent as GET ?userId=...)
            user_id = event.get('queryStringParameters', {}).get('userId')

        if not user_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing userId'})
            }

        print("Extracted userId:", user_id)

        # Initialize DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('UserData')

        # Query using userId as partition key
        response = table.query(
            KeyConditionExpression=Key('userId').eq(user_id)
        )

        print("DynamoDB Items:", response['Items'])

        # Return items to frontend
        return {
            'statusCode': 200,
            'headers': {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": True
            },
            'body': json.dumps(response['Items'])
        }

    except Exception as e:
        print("Error:", str(e))
        return {
            'statusCode': 500,
            'headers': {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": True
            },
            'body': json.dumps({'error': str(e)})
        }
