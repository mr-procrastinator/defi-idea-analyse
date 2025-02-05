import json
import boto3
import os
from dotenv import load_dotenv
from tools import ask_model

load_dotenv()  # Load environment variables from .env file

def send_topic_message(message: dict, subject: str) -> bool:
    """
    Sends a message to an SNS topic.

    Args:
        message (dict): The message to send to the topic
        subject (str): The subject line for the SNS message

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        sns = boto3.client('sns',
                          aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                          aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                          region_name=os.getenv('AWS_DEFAULT_REGION'))
        
        topic_arn = os.getenv('SNS_TOPIC_ARN')
        if not topic_arn:
            raise ValueError("SNS_TOPIC_ARN environment variable is not set")
            
        sns.publish(
            TopicArn=topic_arn,
            Message=str(message),
            Subject=subject
        )
        return True
    except Exception as e:
        print(f"Error sending message to topic: {str(e)}")
        return False


def add_opinion(opinion_id: str, opinion: str):
    """
    Adds an opinion to the DynamoDB table.

    Args:
        opinion_id (str): The ID to associate the opinion with
        opinion (str): The opinion text to add

    Returns:
        bool: True if successful, False otherwise
    """
    dynamodb = boto3.client('dynamodb',
                          aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                          aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                          region_name=os.getenv('AWS_DEFAULT_REGION'))
    table_name = 'defi_ideas'

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
        
        if send_topic_message(message, f'New Opinion Added for ID: {opinion_id}'):
            return True
        return False
    except Exception as e:
        print(f"Error adding opinion: {str(e)}")
        return False


def get_chat_id(bot_id: str):
    """
    Retrieves the chat ID based on the bot ID and chat name.
    Chat name could be not exact: the function performs fuzzy search.

    Args:
        bot_id (str): The ID of the bot.
        chat_name (str): The name of the chat to retrieve the ID for.
        default_id (str, optional): The default chat ID to return
           if no match is found. Defaults to DEFAULT_CHAT_ID.

    Returns:
        str: The chat ID corresponding to the provided bot ID and
           chat name, or the default ID if no match is found.
    """
    dynamodb = boto3.client('dynamodb',
                          aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                          aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                          region_name=os.getenv('AWS_DEFAULT_REGION'))
    table_name = 'defi_ideas'

    response = dynamodb.get_item(
        TableName=table_name,
        Key={
            'opinionId': {'S': bot_id}
            }
    )

    chats = response['Item'].get('opinions', {}).get('L', [])
    chat_names = [chat.get('S', '') for chat in chats]
    
    print(f"No close match found for the chat name '{chat_names}'.")


def execute_agent(text: str) -> str:
    """
    Executes the Bedrock agent with the provided text.

    Args:
        text (str): The input text to send to the agent

    Returns:
        str: The agent's response
    """
    try:
        bedrock_runtime = boto3.client(
            service_name='bedrock-agent-runtime',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name='us-east-1'
        )

        response = bedrock_runtime.invoke_agent(
            agentId='8XKYWCYSLP',
            agentAliasId='TSTALIASID',  # Using the default alias ID
            sessionId='test-session',  # You might want to make this dynamic
            inputText=text
        )

        # Extract the agent's response from the response object
        agent_response = response['completion']
        final_answer = None
        try:
            for event in agent_response:
                if 'chunk' in event:
                    data = event['chunk']['bytes']
                    final_answer = data.decode('utf8')
                    print(f"Final answer ->\n{final_answer}")
                    end_event_received = True
                elif 'trace' in event:
                    print(json.dumps(event['trace'], indent=2))
                else: 
                    raise Exception("unexpected event.", event)
        except Exception as e:
            raise Exception("unexpected event.",e)
        return agent_response

    except Exception as e:
        print(f"Error executing Bedrock agent: {str(e)}")
        return f"Error: {str(e)}"


if __name__ == "__main__":
    # Example usage
    bot_id = "serg_defi"
    chat_name = "Example Chat"
    
    try:
        # Test the Bedrock agent
        response = execute_agent("opinionId:serg_defi  opinion:What are the latest DeFi trends?")
        print(f"Agent response: {response}")
        message = {
            'opinionId': "serg_defi",
            'newOpinion': "op"
        }
        #add_opinion(bot_id, chat_name)
        # get_chat_id(bot_id)
        #ask_model("Hello", "You are assistant")
        print(f"Found chat ID:")
    except Exception as e:
        print(f"Error getting chat ID: {str(e)}")