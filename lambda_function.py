import boto3
import os

from tools import ask_model


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

def add_opinion(opinion_id: str, opinion: str):
    """
    Adds an opinion to the DynamoDB table and publishes notification to SNS.

    Args:
        opinion_id (str): The ID to associate the opinion with
        opinion (str): The opinion text to add

    Returns:
        bool: True if successful, False otherwise
    """
    dynamodb = boto3.client('dynamodb',
                          region_name='eu-central-1')
    sns = boto3.client('sns', region_name='eu-central-1')
    table_name = 'defi_ideas'
    topic_arn = 'arn:aws:sns:eu-central-1:035586480742:defi-opinions-topic'

    try:
        # First, get the existing item
        response = dynamodb.get_item(
            TableName=table_name,
            Key={
                'opinionId': {'S': opinion_id}
            }
        )

        # If item exists, append to existing opinions
        if 'Item' in response:
            existing_opinions = response['Item'].get('opinions', {}).get('L', [])
            updated_opinions = existing_opinions + [{'S': opinion}]
        else:
            # If item doesn't exist, create new list with the opinion
            updated_opinions = [{'S': opinion}]

        # Update/Create the item in DynamoDB
        dynamodb.put_item(
            TableName=table_name,
            Item={
                'opinionId': {'S': opinion_id},
                'opinions': {'L': updated_opinions}
            }
        )

        # Publish notification to SNS
        message = {
            'opinionId': opinion_id,
            'newOpinion': opinion,
            'totalOpinions': len(updated_opinions)
        }
        
        sns.publish(
            TopicArn=topic_arn,
            Message=str(message),
            Subject=f'New Opinion Added for ID: {opinion_id}'
        )
        
        return True
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
        opinion_id = next(item["value"] for item in parameters if item["name"] == "opinionId")
        opinion = next(item["value"] for item in parameters if item["name"] == "opinion")
        success = add_opinion(opinion_id, opinion)
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
