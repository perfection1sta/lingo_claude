import os
from twilio.rest import Client
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.messages import SystemMessage
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from uuid import uuid4

#LangSmith API setup for LLM Tracing
unique_id = uuid4().hex[0:8]
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = f"Duo_Claude - {unique_id}"

#Authorising Twilio Whatsapp Bot using Environment Variables
account_sid = os.environ.get("TWILIO_SID")
auth_token = os.environ.get("TWILIO_API_KEY")
client = Client(account_sid, auth_token)

#API from environment variable for Claude3 LLM
anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessage(
            content="""You are a conversational language chatbot having a casual with a human about any interests, 
            hobbies & findings. If the conversation if naturally saturating start a new topic. 
            
            Your goal is to act as a Spanish teacher. Give suggesstions & improvements on any 
            gramatical errors & continue the conversation. Ignore typos"""
        ),  # The persistent system prompt
        MessagesPlaceholder(
            variable_name="chat_history"
        ),  # Where the memory will be stored.
        HumanMessagePromptTemplate.from_template(
            "{human_input}"
        ),  # Where the human input will injected
    ]
)

# Configure Conversational memory & Langchain's ChatAnthropic variables
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

llm = ChatAnthropic(
    anthropic_api_key=anthropic_key,
    model_name="claude-3-sonnet-20240229",  # change "opus" -> "sonnet" for speed
    temperature=0.0
)
llm_chain = LLMChain(
    llm=llm,
    prompt=prompt,
    verbose=False, # set this to True to debug ConversationBuffer
    memory=memory,
)

def claude_response(user_response):
	duo_bot_predict = llm_chain.predict(human_input=f"{user_response}")
	return duo_bot_predict

# Initiate Flask app
app = Flask(__name__)

@app.route("/whatsapp", methods=["POST"])
def duo_bot():

	# user input
	user_msg = request.values.get('Body', '').lower()
	bot_answer = claude_response(user_response=user_msg)
	
	# creating object of MessagingResponse
	response = MessagingResponse()
	response.message(bot_answer)
	
	return str(response)

if __name__ == "__main__":
	app.run(debug=True,port=8080)
