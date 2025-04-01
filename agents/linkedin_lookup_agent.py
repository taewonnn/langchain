import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool
from langchain.agents import (create_react_agent, AgentExecutor)
from langchain import hub


load_dotenv()


def lookup(name: str) -> str:
    llm = ChatOpenAI(
        temparature=0,
        model_name="gpt-4o-mini"
    )


    return 'https://www.linkedin.com/in/eden-marco'

