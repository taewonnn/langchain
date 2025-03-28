import os
from dotenv import load_dotenv


load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

if __name__ == '__main__':
    print('hello!')
