import os
import time
import pandas as pd
from pprint import pprint
import streamlit as st

from langchain.chat_models import ChatOpenAI
from langchain.schema import Document
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Pinecone as PineconeVectorStore
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
import pinecone


pinecone.Index = pinecone.data.index.Index

# 환경변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
INDEX_NAME = os.getenv('INDEX_NAME')

# Streamlit UI 설정
st.title("ADN Keyword Matching")
query = st.text_input("질문을 입력하세요", value="")

# dataframe 로드 및 전처리
df = pd.read_csv('./data/log_keyword.csv')
filtered_list = df[['ui', 'ad_ids', 'k']].dropna()
st.write(filtered_list.head(100))

# Pinecone 초기화 및 인덱스 생성
pc = Pinecone(api_key=PINECONE_API_KEY)
existing_indexes = pc.list_indexes().names()
if INDEX_NAME not in existing_indexes:
    pc.create_index(
        name=INDEX_NAME,
        dimension=1536,
        metric='euclidean',
        spec=ServerlessSpec(
            cloud='aws',
            region='us-east-1'
        )
    )

# CSV 데이터 각 행을 Document로 변환
docs = []
for i, (_, row) in enumerate(filtered_list.iterrows()):
    text = f"ui: {row['ui']}\nad_ids: {row['ad_ids']}\nk: {row['k']}"
    doc = Document(
        page_content=text,
        metadata={**row.to_dict(), "id": f"doc_{i}"}  # 고유 id 지정 -> 중복 방지
    )
    docs.append(doc)

# embedding 생성
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

# PineconeVectorStore를 통해 Document 업서트
vectorstore = PineconeVectorStore.from_documents(
    docs,
    embedding=embeddings,
    index_name=INDEX_NAME
)

# Prompt Template
prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template="""
        아래 문서들을 참고하여, '{question}'와 관련되어 보이는 모든 키워드를 추출해줘.
        각 키워드에 대해, 해당 키워드가 등장한 문서의 'ui', 'ad_ids', 그리고 원래 키워드('k') 정보를 함께 나열해줘.

        문서:
        {context}

        답변은 다음 형식으로 작성해줘:
        ui: <ui 정보>
        ad_ids: <ad_ids 정보>
        k: <키워드>

        모든 관련 키워드를 누락 없이 출력해줘.
    """
)

# Retrieval QA 체인 구성 및 쿼리 실행
retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 100})
qa = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(openai_api_key=OPENAI_API_KEY),
    chain_type="stuff",
    retriever=retriever,
    chain_type_kwargs={"prompt": prompt_template}
)

if st.button("질문하기"):
    with st.spinner("처리 중..."):
        result = qa.run(query)
    st.success("완료!")
    st.text_area("답변", value=result, height=900)
