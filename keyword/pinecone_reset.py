import os
import pinecone
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

load_dotenv()
PINECONE_API_KEY= os.getenv('PINECONE_API_KEY')
PINECONE_HOST= os.getenv('PINECONE_HOST')


# Pinecone record Reset
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(host=PINECONE_HOST)
index.delete(delete_all=True)