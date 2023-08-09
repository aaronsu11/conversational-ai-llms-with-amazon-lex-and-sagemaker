"""Lambda that acts as the fulfillment hook for either a Lex bot or the QnABot on AWS Solution
"""
from dispatchers.LexV2SMLangchainDispatcher import LexV2SMLangchainDispatcher
from dispatchers.QnABotSMLangchainDispatcher import QnABotSMLangchainDispatcher
from dispatchers import utils
import logging
import boto3
import json

logger = utils.get_logger(__name__)
logger.setLevel(logging.DEBUG)

# Initialize IoT client
iot_client = boto3.client("iot-data", region_name='us-east-1')


def dispatch_lexv2(request):
    """Summary

    Args:
        request (dict): Lambda event containing an user's input chat message and context (historical conversation)
        Uses the LexV2 sessions API to manage past inputs https://docs.aws.amazon.com/lexv2/latest/dg/using-sessions.html

    Returns:
        dict: Description
    """
    lexv2_dispatcher = LexV2SMLangchainDispatcher(request)
    return lexv2_dispatcher.dispatch_intent()


def dispatch_qnabot(request):
    """Summary

    Args:
        request (dict): Lambda event containing an user's input chat message and context (historical conversation)

    Returns:
        dict: Dict formated as documented to be a lambda hook for a "don't know" answer for the QnABot on AWS Solution
        see https://docs.aws.amazon.com/solutions/latest/qnabot-on-aws/specifying-lambda-hook-functions.html
    """
    request["res"]["message"] = "Hi! This is your Custom Python Hook speaking!"
    qna_intent_dispatcher = QnABotSMLangchainDispatcher(request)
    return qna_intent_dispatcher.dispatch_intent()


def push_to_iot(message):
    """Push a message to AWS IoT Core"""

    # Assuming you have a topic named 'pupperTopic'
    topic = "pupper"

    iot_client.publish(topic=topic, qos=1, payload=json.dumps(message))


def lambda_handler(event, context):
    print(event)
    if "sessionState" in event:
        if "intent" in event["sessionState"]:
            if "name" in event["sessionState"]["intent"]:
                if event["sessionState"]["intent"]["name"] == "FallbackIntent":
                    return dispatch_lexv2(event)
                elif event["sessionState"]["intent"]["name"] == "PupperDance":
                    push_to_iot({"move": "dance"})
                    return utils.close(
                        event,
                        utils.get_session_attributes(event),
                        "Fulfilled",
                        {
                            "contentType": "PlainText",
                            "content": '{"speak": "", "act": "happy", "move": "dance"}',
                        },
                    )
                elif event["sessionState"]["intent"]["name"] == "PupperStop":
                    push_to_iot({"move": "stop"})
                    return utils.close(
                        event,
                        utils.get_session_attributes(event),
                        "Fulfilled",
                        {
                            "contentType": "PlainText",
                            "content": '{"speak": "", "act": "none", "move": "stop"}',
                        },
                    )

    else:
        return dispatch_qnabot(event)


if __name__ == "__main__":
    event = {
        "sessionId": "177118830501985",
        "inputTranscript": "Dance",
        "interpretations": [
            {
                "intent": {
                    "name": "PupperDance",
                    "slots": {},
                    "state": "ReadyForFulfillment",
                    "confirmationState": "None",
                },
                "nluConfidence": 1,
            },
            {
                "intent": {
                    "name": "FallbackIntent",
                    "slots": {},
                    "state": "ReadyForFulfillment",
                    "confirmationState": "None",
                }
            },
            {
                "intent": {
                    "name": "PupperStop",
                    "slots": {},
                    "state": "ReadyForFulfillment",
                    "confirmationState": "None",
                },
                "nluConfidence": 0.48,
            },
        ],
        "bot": {
            "name": "Sagemaker-Jumpstart-Flan-LLM-Fallback-Bot",
            "version": "DRAFT",
            "localeId": "en_US",
            "id": "25SKAUSDGZ",
            "aliasId": "TSTALIASID",
            "aliasName": "TestBotAlias",
        },
        "responseContentType": "text/plain; charset=utf-8",
        "sessionState": {
            "sessionAttributes": {},
            "intent": {
                "name": "PupperDance",
                "slots": {},
                "state": "ReadyForFulfillment",
                "confirmationState": "None",
            },
            "originatingRequestId": "322f9283-851d-493a-8fa8-49b89a0b6778",
        },
        "messageVersion": "1.0",
        "invocationSource": "FulfillmentCodeHook",
        "transcriptions": [
            {
                "resolvedContext": {"intent": "PupperDance"},
                "transcription": "Dance",
                "resolvedSlots": {},
                "transcriptionConfidence": 1,
            }
        ],
        "inputMode": "Text",
    }

    lambda_handler(event, None)
