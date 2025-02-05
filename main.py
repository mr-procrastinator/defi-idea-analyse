from telethon import TelegramClient, events, sync
import json
import boto3
import os
from dotenv import load_dotenv
from tools import ask_model

load_dotenv()


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
        print('start processing')
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
            print('processed')
        except Exception as e:
            raise Exception("unexpected event.",e)
        return agent_response

    except Exception as e:
        print(f"Error executing Bedrock agent: {str(e)}")
        return f"Error: {str(e)}"

# Get Telegram API credentials from environment variables
api_id = os.getenv('TELEGRAM_API_KEY')
api_hash = os.getenv('TELEGRAM_API_HASH')

client = TelegramClient('session_name', api_id, api_hash, system_version="4.16.30-vxCUSTOM")
client.start()


source_channel = "@defi_opinion"

 
@client.on(events.NewMessage(chats=source_channel))
async def handler(event):
    message = event.message
    #print(event)
    data =f'''
    <opinionId>serg_defi</opinionId> <opinion>{message.message}</opinion>
    '''
    execute_agent(data)
    #await client.send_message(destination_group, message, reply_to=187)

client.run_until_disconnected()