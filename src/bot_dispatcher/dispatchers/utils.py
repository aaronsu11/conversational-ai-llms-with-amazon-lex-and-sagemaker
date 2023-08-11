import logging
import os
import boto3
import re
import json

# Initialize IoT client
iot_client = boto3.client("iot-data", region_name="us-east-1")

def get_logger(module_name):

    logger = logging.getLogger(module_name)
    logger.propagate = False
    logger.setLevel(logging.INFO)

    if "DEBUG" in os.environ and os.environ["DEBUG"] == "true":
        logger.setLevel(logging.DEBUG)

    return logger


def get_slots(intent_request):
    return intent_request['sessionState']['intent']['slots']


def get_slot(intent_request, slotName):
    slots = get_slots(intent_request)
    if slots is not None and slotName in slots and slots[slotName] is not None:
        return slots[slotName]['value']['interpretedValue']
    else:
        return None


def get_session_attributes(intent_request):
    sessionState = intent_request['sessionState']
    if 'sessionAttributes' in sessionState:
        return sessionState['sessionAttributes']
    return {}


def elicit_intent(intent_request, session_attributes, message):
    return {
        'sessionState': {
            'dialogAction': {
                'type': 'ElicitIntent'
            },
            'sessionAttributes': session_attributes
        },
        'messages': [message] if message != None else None,
        'requestAttributes': intent_request['requestAttributes'] if 'requestAttributes' in intent_request else None
    }


def close(intent_request, session_attributes, fulfillment_state, message):
    intent_request['sessionState']['intent']['state'] = fulfillment_state
    return {
        'sessionState': {
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'Close'
            },
            'intent': intent_request['sessionState']['intent']
        },
        'messages': [message],
        'sessionId': intent_request['sessionId'],
        'requestAttributes': intent_request['requestAttributes'] if 'requestAttributes' in intent_request else None
    }

def push_to_iot(message: dict, session_id: str):
    """Push a message to AWS IoT Core"""

    match = re.match(r'^([^-]+)-', session_id)
    if match:
        pupper_name = match.group(1)
    else:
        pupper_name = "default"

    # Assuming you have a topic named 'pupperTopic'
    topic = f"pupper/{pupper_name}"

    iot_client.publish(topic=topic, qos=1, payload=json.dumps(message))
