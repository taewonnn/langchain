import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from third_parties.linkedin import scrape_linkedin_profile


# env
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")


# PromptTemplate
summary_template = """
    given the linkedin inforamtion about a person from I want you to create
    Please answer in korean
    1. a short summary
    2. two interesting facts about them
"""

summary_prompt_template = PromptTemplate(
    input_variables=['information'], template=summary_template
)

llm = ChatOpenAI(temperature=0, model_name='gpt-3.5-turbo')

chain = summary_prompt_template | llm | StrOutputParser()

linkedin_data = scrape_linkedin_profile(linkedin_profile_url='https://gist.githubusercontent.com/emarco177/859ec7d786b45d8e3e3f688c6c9139d8/raw/32f3c85b9513994c572613f2c8b376b633bfc43f/eden-marco-scrapin.json')
res = chain.invoke(input={"information": linkedin_data})

print(res)



