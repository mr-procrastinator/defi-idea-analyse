import json
import os
import boto3
from typing import Union

from dotenv import load_dotenv

load_dotenv()

def ask_model(messages: str, instructions: str) -> str:
    """
    Generates responses from a language model based on chat messages and instructions.

    Args:
        messages (str): The chat messages to be used as context for generating responses.
        instructions (str): Additional instructions or question to provide to the model.

    Returns:
        str: The generated response from the language model.
    """
    if not messages:
        return "No messages was found. Consider using other chat."

    prompt = str(messages) + instructions

    prompt_config = {
        "inputText": prompt,
        "textGenerationConfig": {
            "maxTokenCount": 1000,
            "stopSequences": [],
            "temperature": 1,
            "topP": 1,
        },
    }

    body = json.dumps(prompt_config)

    bedrock_runtime = boto3.client(
        service_name='bedrock-runtime',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                          aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name='us-east-1'
    )

    model_id = "amazon.titan-text-lite-v1"
    accept = "application/json"
    content_type = "application/json"

    response = bedrock_runtime.invoke_model(
        body=body, modelId=model_id, accept=accept, contentType=content_type
    )
    response_body = json.loads(response.get("body").read())

    results = response_body.get("results")[0].get("outputText")
    return results
