import boto3
import os
from dotenv import load_dotenv
import requests
import time
import json

from tools import ask_model
from defillama import process_invest_idea

load_dotenv()
# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

def store_user(user_id: int, first_name: str, username: str) -> bool:
    """
    Store user information in DynamoDB.
    Args:
        user_id (int): Telegram user ID
        first_name (str): User's first name
        username (str): User's username
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        dynamodb = boto3.client('dynamodb',
                            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                            region_name='eu-central-1')
        
        dynamodb.put_item(
            TableName='telegram_users',
            Item={
                'user_id': {'S': str(user_id)},
                'first_name': {'S': first_name or 'Unknown'},
                'username': {'S': username or 'Unknown'},
                'last_active': {'S': time.strftime('%Y-%m-%d %H:%M:%S')}
            }
        )
        print(f"Stored/Updated user in DynamoDB: {user_id}")
        return True
    except Exception as e:
        print(f"Error storing user in DynamoDB: {str(e)}")
        return False

def get_stored_users() -> set:
    """
    Get all users from DynamoDB.
    Returns:
        set: Set of tuples containing (user_id, first_name, username)
    """
    try:
        dynamodb = boto3.client('dynamodb',
                            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                            region_name='eu-central-1')
        
        response = dynamodb.scan(TableName='telegram_users')
        users = set()
        for item in response.get('Items', []):
            user_tuple = (
                int(item['user_id']['S']),
                item['first_name']['S'],
                item['username']['S']
            )
            users.add(user_tuple)
        print(f"Retrieved {len(users)} users from DynamoDB")
        return users
    except Exception as e:
        print(f"Error getting users from DynamoDB: {str(e)}")
        return set()

def get_bot_users() -> set:
    """Get all unique users who have interacted with the bot"""
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    users = get_stored_users()  # Get existing users from DynamoDB
    
    try:
        print(f"Fetching recent bot users from Telegram API")
        params = {
            'offset': -1,  # Start from the beginning
            'limit': 100   # Get maximum allowed updates
        }
        response = requests.get(telegram_url, params=params)
        print(f"GetUpdates response status: {response.status_code}")
        
        if response.ok:
            result = response.json()
            updates = result['result']
            print(f"Found {len(updates)} recent updates")
            
            if len(updates) == 0 and not users:
                print("No users found in both DynamoDB and recent updates")
                test_user = (880083906, "TestUser", "test_username")
                users.add(test_user)
                store_user(*test_user)  # Store test user in DynamoDB
                print(f"Added test user for debugging: {test_user}")
            
            for update in updates:
                if 'message' in update:
                    user = update['message']['from']
                    user_tuple = (
                        user['id'], 
                        user.get('first_name', 'Unknown'), 
                        user.get('username', 'Unknown')
                    )
                    users.add(user_tuple)
                    # Store or update user in DynamoDB
                    store_user(*user_tuple)
                    print(f"Added/Updated user: {user_tuple}")
        
        print(f"Total unique users found: {len(users)}")
        return users
    except Exception as e:
        print(f"Error getting bot users: {str(e)}")
        if 'response' in locals():
            print(f"Response content: {response.text}")
        return users  # Return stored users even if API call fails

def broadcast_message(users, message):
    """
    Send message to all users
    
    Args:
        users (set): Set of tuples containing (user_id, first_name, username)
        message (str): Message to broadcast to all users
    
    Returns:
        bool: True if all messages were sent successfully, False otherwise
    """
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    success = True
    successful_sends = 0
    failed_sends = 0
    
    print(f"\n=== Starting broadcast to {len(users)} users ===")
    print(f"Message length: {len(message)} characters")
    
    for user_id, first_name, username in users:
        try:
            print(f"\nAttempting to send to user: {user_id} ({first_name}, @{username})")
            payload = {
                "chat_id": user_id,
                "text": message,
                "parse_mode": "HTML"
            }
            
            response = requests.post(telegram_url, json=payload)
            print(f"Response status code: {response.status_code}")
            
            if not response.ok:
                print(f"Error sending Telegram message to user {user_id}")
                print(f"Response content: {response.text}")
                success = False
                failed_sends += 1
            else:
                print(f"Successfully sent message to user {user_id}")
                successful_sends += 1
            
            # Sleep briefly to avoid hitting rate limits
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Exception while sending to user {user_id}: {str(e)}")
            success = False
            failed_sends += 1
    
    print(f"\n=== Broadcast completed ===")
    print(f"Successful sends: {successful_sends}")
    print(f"Failed sends: {failed_sends}")
    print(f"Overall success: {success}")
    
    return success

def summarize_messages(parameters: list) -> str:
    """
    Summarizes messages extracted from a chat.

    Args:
        parameters (list): A list of dictionaries containing parameters
            related to the chat. Each dictionary contains 'name' and 'value'
            keys, where 'name' represents the parameter name and 'value'
            represents the parameter value.

    Returns:
        str: A summary of the chat and extracted action points.
    """
    messages = next(item["value"] for item in parameters if item["name"] == "messages")
    instructions = "Given the messages extracted from the chat, summarize.\n"
    return ask_model(messages, instructions)

def translate_messages(parameters: list) -> str:
    """
    Translates messages from a specified source language to English.

    Args:
        parameters (list): A list of dictionaries containing parameters
            related to the translation. Each dictionary contains 'name' and 'value'
            keys, where 'name' represents the parameter name and 'value'
            represents the parameter value.

    Returns:
        str: Translated messages in English.
    """
    messages = next(item["value"] for item in parameters if item["name"] == "messages")
    source_lang = next(item["value"] for item in parameters if item["name"] == "sourceLanguage")
    if not messages:
        return "No messages was found. Consider using other chat."
    client = boto3.client('translate', region_name='us-east-1')

    response = client.translate_text(
            Text=messages,
            SourceLanguageCode=source_lang,
            TargetLanguageCode='en'
        )

    translated_message = response['TranslatedText']

    return translated_message

def detect_language(parameters: list) -> str:
    """
    Detects the language of messages.

    Args:
        parameters (list): A list of dictionaries containing parameters
            related to the chat. Each dictionary contains 'name' and 'value'
            keys, where 'name' represents the parameter name and 'value'
            represents the parameter value.

    Returns:
        str: Language code, for example 'pl'.
    """
    messages = next(item["value"] for item in parameters if item["name"] == "messages")
    if not messages:
        return "No messages was found. Consider using other chat."
    comprehend = boto3.client('comprehend')

    response = comprehend.detect_dominant_language(Text=messages)
    detected_language = response['Languages'][0]['LanguageCode']

    return detected_language

def add_opinion(user_id: str, opinion: str):
    """
    Adds an opinion to the DynamoDB table and broadcasts notification to all Telegram bot users.

    Args:
        opinion_id (str): The ID to associate the opinion with
        opinion (str): The opinion text to add

    Returns:
        bool: True if successful, False otherwise
    """
    dynamodb = boto3.client('dynamodb',
                               aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                            region_name='eu-central-1')
    table_name = 'defi_ideas'

    try:
        print(f"Adding opinion for user {user_id}: {opinion}")
        data = process_invest_idea(opinion)
        print(f"Processed data: {data}")

        # First, get the existing item
        response = dynamodb.get_item(
            TableName=table_name,
            Key={
                'opinionId': {'S': user_id}
            }
        )

        # If item exists, append to existing opinions
        if 'Item' in response:
            existing_opinions = response['Item'].get('opinions', {}).get('L', [])
            updated_opinions = existing_opinions + [{'S': data}]
        else:
            # If item doesn't exist, create new list with the opinion
            updated_opinions = [{'S': data}]

        # Update/Create the item in DynamoDB
        dynamodb.put_item(
            TableName=table_name,
            Item={
                'opinionId': {'S': user_id},
                'opinions': {'L': updated_opinions}
            }
        )

        # Send SNS notification if user is system
        if user_id == 'system':
            try:
                sns = boto3.client('sns', region_name='eu-central-1')
                sns_payload = {
                    "opinionId": "system",
                    "opinion": data
                }
                sns.publish(
                    TopicArn='arn:aws:sns:eu-central-1:035586480742:defi-opinions-topic',
                    Message=json.dumps(sns_payload)
                )
                print("Successfully sent SNS notification")
            except Exception as e:
                print(f"Error sending SNS notification: {str(e)}")
                # Continue execution even if SNS fails

        # Get all bot users
        users = get_bot_users()
        if not users:
            print("No users found to send notifications to")
            return True  # Still return True as DynamoDB operation was successful

        # Prepare message
        if user_id == 'system':
            message = f"🔔 New Investment Idea: \n\n" \
                      f"{data}\n"
        else:
            message = f"🔔 Processed Investment Idea: \n\n" \
                    f"{data}\n" 

        # Broadcast message to all users
        return broadcast_message(users, message)
    except Exception as e:
        print(f"Error adding opinion: {str(e)}")
        return False

def lambda_handler(event: dict, context: object) -> dict:
    """
    Lambda function handler to process incoming API requests.

    Args:
        event (dict): The event data passed to the lambda function.
        context (object): The runtime information of the lambda function.

    Returns:
        dict: A dictionary containing the response data to be returned
           by the lambda function.

    """
    print("Received event: ")
    print(event)

    response_code = None
    action = event["actionGroup"]
    api_path = event["apiPath"]
    parameters = event.get("parameters", None)
    if not parameters:
        parameters = event['requestBody']['content']['application/json']['properties']
    http_method = event["httpMethod"]

    if api_path == '/detect-language':
        body = detect_language(parameters)
        response_body = {"application/json": {"body": str(body)}}
        response_code = 200
    elif api_path == '/translate':
        body = translate_messages(parameters)
        response_body = {"application/json": {"body": str(body)}}
        response_code = 200
    elif api_path == '/summarize':
        body = summarize_messages(parameters)
        response_body = {"application/json": {"body": str(body)}}
        response_code = 200
    elif api_path == '/add-opinion':
        user_id = next(item["value"] for item in parameters if item["name"] == "userId")
        opinion = next(item["value"] for item in parameters if item["name"] == "opinion")
        success = add_opinion(user_id, opinion)
        response_code = 200 if success else 500
        response_body = {"application/json": {"body": str(success)}}
    else:
        body = {"{}::{} is not a valid api, try another one.".format(action, api_path)}
        response_code = 400
        response_body = {"application/json": {"body": str(body)}}

    print(f"Response body: {response_body}")

    action_response = {
        "actionGroup": action,
        "apiPath": api_path,
        "httpMethod": http_method,
        "httpStatusCode": response_code,
        "responseBody": response_body,
    }

    api_response = {"messageVersion": "1.0", "response": action_response}

    return api_response

if __name__ == "__main__":
    # Test add_opinion function
    test_user_id = "system"
    test_opinion = "I believe ETH will reach $5000 by the end of 2025 due to increased institutional adoption and the growing DeFi ecosystem."
    
    success = add_opinion(test_user_id, test_opinion)
    #broadcast_message(get_bot_users(), "Test message")
    #print(f"Opinion added successfully: {success}")
