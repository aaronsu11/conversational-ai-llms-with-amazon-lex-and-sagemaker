"""Lambda that acts as the fulfillment hook for either a Lex bot or the QnABot on AWS Solution
"""
from dispatchers.LexV2SMLangchainDispatcher import LexV2SMLangchainDispatcher
from dispatchers.QnABotSMLangchainDispatcher import QnABotSMLangchainDispatcher
from dispatchers import utils
import logging

logger = utils.get_logger(__name__)
logger.setLevel(logging.DEBUG)


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


def lambda_handler(event, context):
    print(event)
    if "sessionState" in event:
        if "intent" in event["sessionState"]:
            if "name" in event["sessionState"]["intent"]:
                if event["sessionState"]["intent"]["name"] == "FallbackIntent":
                    return dispatch_lexv2(event)
                elif event["sessionState"]["intent"]["name"] == "PupperDance":
                    utils.push_to_iot({"speak": "", "act": "happy", "move": "dance"}, event["sessionId"])
                    return utils.close(
                        event,
                        utils.get_session_attributes(event),
                        "Fulfilled",
                        {
                            "contentType": "PlainText",
                            "content": "Move it!",
                        },
                    )
                elif event["sessionState"]["intent"]["name"] == "PupperStop":
                    utils.push_to_iot({"speak": "", "act": "none", "move": "stop"}, event["sessionId"])
                    return utils.close(
                        event,
                        utils.get_session_attributes(event),
                        "Fulfilled",
                        {
                            "contentType": "PlainText",
                            "content": "Move it!",
                        },
                    )

    else:
        return dispatch_qnabot(event)


if __name__ == "__main__":
    event = {
        "sessionId": "ngl-b0a4709b-f8c4-4755-b253-38d987256c21",
        "inputTranscript": "what is your name",
        "rawInputTranscript": "what is your name",
        "interpretations": [
            {
                "intent": {
                    "confirmationState": "None",
                    "name": "FallbackIntent",
                    "slots": {},
                    "state": "ReadyForFulfillment",
                }
            },
            {
                "intent": {
                    "confirmationState": "None",
                    "name": "PupperDance",
                    "slots": {},
                    "state": "ReadyForFulfillment",
                },
                "nluConfidence": 0.77,
            },
            {
                "intent": {
                    "confirmationState": "None",
                    "name": "PupperStop",
                    "slots": {},
                    "state": "ReadyForFulfillment",
                },
                "nluConfidence": 0.46,
            },
        ],
        "bot": {
            "aliasId": "DDZZ2QXCJT",
            "aliasName": "prod",
            "name": "Sagemaker-Jumpstart-Flan-LLM-Fallback-Bot",
            "version": "2",
            "localeId": "en_US",
            "id": "25SKAUSDGZ",
        },
        "responseContentType": "audio/pcm",
        "sessionState": {
            "sessionAttributes": {},
            "intent": {
                "confirmationState": "None",
                "name": "FallbackIntent",
                "slots": {},
                "state": "ReadyForFulfillment",
            },
            "originatingRequestId": "f9a0ef45-161a-4141-91fe-fbea852ec9bc",
        },
        "messageVersion": "1.0",
        "invocationSource": "FulfillmentCodeHook",
        "inputMode": "Speech",
    }

    lambda_handler(event, None)
