"""Summary
"""
from typing import List, Any, Dict
from pydantic import BaseModel, Extra
import json

from langchain import PromptTemplate, SagemakerEndpoint, ConversationChain
from langchain.schema import BaseMemory
from langchain.llms.bedrock import Bedrock
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

class LexConversationalMemory(BaseMemory, BaseModel):

    """Langchain Custom Memory class that uses Lex Conversation history
    
    Attributes:
        history (dict): Dict storing conversation history that acts as the Langchain memory
        lex_conv_context (str): LexV2 sessions API that serves as input for convo history
            Memory is loaded from here
        memory_key (str): key to for chat history Langchain memory variable - "history"
    """
    history: dict = {}
    memory_key: str = "chat_history" #pass into prompt with key
    lex_conv_context: str = '{"chat_history": "none"}'

    def clear(self):
        """Clear chat history
        """
        self.history = {}

    @property
    def memory_variables(self) -> List[str]:
        """Load memory variables
        
        Returns:
            List[str]: List of keys containing Langchain memory
        """
        return [self.memory_key]

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, str]:
        """Load memory from lex into current Langchain session memory
        
        Args:
            inputs (Dict[str, Any]): User input for current Langchain session
        
        Returns:
            Dict[str, str]: Langchain memory object
        """
        input_text = inputs[list(inputs.keys())[0]]

        ccontext = json.loads(self.lex_conv_context)
        memory = {
            # self.memory_key: ccontext[self.memory_key] + input_text + "\nAI: ",
            self.memory_key: ccontext[self.memory_key],
        }
        return memory

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """Load memory from lex + current input into Langchain session memory
        
        Args:
            inputs (Dict[str, Any]): User input
            outputs (Dict[str, str]): Langchain response from calling LLM
        """
        input_text = inputs[list(inputs.keys())[0]]
        output_text = outputs[list(outputs.keys())[0]]

        ccontext = json.loads(self.lex_conv_context)
        self.history =  {
            self.memory_key: ccontext[self.memory_key] + input_text + f"\nAI: {output_text}",
        }


class BedrockBot():

    """Create a langchain.ConversationChain using a Sagemaker endpoint as the LLM
    
    Attributes:
        chain (langchain.ConversationChain): Langchain chain that invokes the Sagemaker endpoint hosting an LLM
    """
    
    def __init__(self, prompt_template,
        lex_conv_history="",
        region_name="us-west-2"):
        """Create a SagemakerLangchainBot client
        
        Args:
            prompt_template (str): Prompt template
            sm_endpoint_name (str): Sagemaker endpoint name
            lex_conv_history (str, optional): Lex convo history from LexV2 sessions API. Empty str '{"chat_history": ""}' for no history (first chat)
            region_name (str, optional): region where Sagemaker endpoint is deployed
        """

        prompt = PromptTemplate(
            input_variables=["chat_history", "input"],
            template=prompt_template
        )
        
        # Sagemaker endpoint for the LLM. Pass in arguments for tuning the model and
        llm = Bedrock(
            # credentials_profile_name="bedrock-admin",
            region_name=region_name,
            model_id="amazon.titan-tg1-large",
            model_kwargs={"temperature":0.1},
            endpoint_url="https://prod.us-west-2.frontend.bedrock.aws.dev",
        )

        memory = LexConversationalMemory(lex_conv_context=lex_conv_history) if lex_conv_history else LexConversationalMemory()
        
        # Create a conversation chain using the prompt, llm hosted in Sagemaker, and custom memory class
        self.chain = ConversationChain(
            llm=llm, 
            prompt=prompt, 
            memory=memory,
            verbose=True
        )

    def call_llm(self,user_input) -> str:
        """Call the Sagemaker endpoint hosting the LLM by calling ConversationChain.predict()
        
        Args:
            user_input (str): User chat input
        
        Returns:
            str: Sagemaker response to display as chat output
        """
        output = self.chain.predict(
            input=user_input
        )
        print("call_llm - input :: "+user_input)
        print("call_llm - output :: "+output)
        return output 