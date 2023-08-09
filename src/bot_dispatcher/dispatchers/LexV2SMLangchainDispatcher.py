from dispatchers import utils
from sm_utils.bedrock_langchain_sample import BedrockBot
import json
import os
import logging

logger = utils.get_logger(__name__)
logger.setLevel(logging.DEBUG)
CHAT_HISTORY="chat_history"
initial_history = {CHAT_HISTORY: f"AI: Hi there! How Can I help you?\nHuman: ",}

class LexV2SMLangchainDispatcher():

    def __init__(self, intent_request):
        # See lex bot input format to lambda https://docs.aws.amazon.com/lex/latest/dg/lambda-input-response-format.html
        self.intent_request = intent_request
        self.localeId = self.intent_request['bot']['localeId']
        self.input_transcript = self.intent_request['inputTranscript'] # user input
        self.session_attributes = utils.get_session_attributes(
            self.intent_request)
        self.fulfillment_state = "Fulfilled"
        self.text = "" # response from endpoint
        self.message = {'contentType': 'PlainText','content': self.text}

    def dispatch_intent(self):

        # define prompt
        prompt_template = """You are an AI robot named "mini pupper" that can only do 2 types of actions: speak and act.
- "speak" action can have any content in a conversational style
- "act" action can only be a range of facial expressions: happy, angry, sad, none.

You are having a conversation with a human and you are talkative, friendly and humorous. If you do not know the answer to a question, you truthfully says you don't know.

As a robot, you must always respond with a JSON object containing the actions and nothing else. 

The JSON object must comply with the following format:
---
{{"speak": <str>, "act": <str>}}
---

For example:

Human: Hi, what's your name?
Robot: {{"speak": "My name is mini pupper!", "act": "happy"}}

Human: I hate you!
Robot: {{"speak": "Oh no! I'm just a mini pupper trying to spread happiness.", "act": "sad"}}

Conversation History:
{chat_history}

Now respond to the Human message below in a JSON object with the appropriate actions.

Human: {input}
Robot: """
        
        # Set context with convo history for custom memory in langchain
        conv_context: str = self.session_attributes.get('ConversationContext', json.dumps(initial_history))
        print("context retrieved:" + conv_context)
        conv_context_json = json.loads(conv_context)

        logger.debug(conv_context_json)

        # LLM
        langchain_bot = BedrockBot(
            prompt_template = prompt_template,
            region_name = os.environ.get('AWS_REGION',"us-west-2"),
            lex_conv_history = conv_context
        )

        llm_response = langchain_bot.call_llm(user_input=self.input_transcript)
        print("llm_response:: " + llm_response)

        
        self.message = {
            'contentType': 'PlainText',
            'content': llm_response
        }

        # save chat history as Lex session attributes
        session_conv_context = json.loads(conv_context)
        session_conv_context[CHAT_HISTORY] = session_conv_context[CHAT_HISTORY] + self.input_transcript + f"\nAI: {llm_response}" +"\nHuman: "
        self.session_attributes["ConversationContext"] = json.dumps(session_conv_context)

        self.response = utils.close(
            self.intent_request, 
            self.session_attributes, 
            self.fulfillment_state, 
            self.message
        )

        return self.response