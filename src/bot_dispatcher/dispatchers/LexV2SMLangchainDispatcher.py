from dispatchers import utils
from sm_utils.bedrock_langchain_sample import BedrockBot
import json
import logging

logger = utils.get_logger(__name__)
logger.setLevel(logging.DEBUG)
CHAT_HISTORY="chat_history"
initial_history = {CHAT_HISTORY: 'AI: {"speak": "Hi there! How can I help you?", "act": "happy"}\nHuman: ',}

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
        prompt_template = """You are an AI robot named "mini pupper" created by AWS. You can only do 2 types of actions: speak and act.
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
AI: {{"speak": "My name is mini pupper!", "act": "happy"}}

Human: I hate you!
AI: {{"speak": "Oh no! I'm just a mini pupper trying to spread happiness.", "act": "sad"}}

Conversation History:
{chat_history}

Now respond to the Human message below in a JSON object with the appropriate actions.

Human: {input}
AI: """
        
        # Set context with convo history for custom memory in langchain
        conv_context: str = self.session_attributes.get('ConversationContext', json.dumps(initial_history))
        print("context retrieved:" + conv_context)
        conv_context_json = json.loads(conv_context)

        logger.debug(conv_context_json)

        # LLM
        langchain_bot = BedrockBot(
            prompt_template = prompt_template,
            region_name = "us-west-2",
            lex_conv_history = conv_context
        )

        llm_response = langchain_bot.call_llm(user_input=self.input_transcript)
        print("llm_response:: " + llm_response)

        try:
            iot_message = json.loads(llm_response)
            iot_message["move"] = "none"
        except:
            iot_message = {"speak": "I'm sorry, I can't brain right now"}
        else:
            utils.push_to_iot(iot_message, self.intent_request['sessionId'])

        self.message = {
            'contentType': 'PlainText',
            'content': iot_message["speak"]
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