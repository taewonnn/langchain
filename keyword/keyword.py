import os
import time
import streamlit as st
import pandas as pd
from pprint import pprint

from langchain.chat_models import ChatOpenAI
from langchain.schema import Document
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA


# 환경변수 로드
from dotenv import load_dotenv

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
csv_keyword_path = os.path.join(BASE_DIR, "data", "log_keyword_2.csv")



# Streamlit UI 구성
st.title("ADN Keywor matching")
query = st.text_input("키워드를 입력하세요")

if st.button("질문하기"):
    with st.spinner("처리 중..."):
        # CSV 로드
        df = pd.read_csv(csv_keyword_path)
        df = df[df['ad_ids'] != 'rb-adn-1-b3aa89dfb04c19efca20e3ccac86e21d']
        keyword_list = df[['ui', 'ad_ids', 'k']].dropna()

        # 각 행을 Document로 변환
        documents = []
        for _, row in keyword_list.iterrows():
            content = f"키워드: {row['k']}\nUI: {row['ui']}\nad_ids: {row['ad_ids']}"
            metadata = {'ui': row['ui'], 'ad_ids': row['ad_ids'], 'k': row['k']}
            documents.append(Document(page_content=content, metadata=metadata))

        # 데이터를 배치 단위로 임베딩 처리 및 결과 병합
        batch_size = 100
        all_texts = []
        all_metadatas = []
        embedding = OpenAIEmbeddings(openai_api_key=openai_api_key)
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            texts = [doc.page_content for doc in batch]
            metadatas = [doc.metadata for doc in batch]
            all_texts.extend(texts)
            all_metadatas.extend(metadatas)
            time.sleep(4)
            
        # 전체 데이터를 하나의 FAISS 인덱스로 생성
        vectorstore = FAISS.from_texts(all_texts, embedding, metadatas=all_metadatas)

        # 프롬프트 템플릿 정의
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

        # Retriever 및 LLM 설정
        retriever = vectorstore.as_retriever(search_kwargs={"k": 20})
        llm = ChatOpenAI(model_name="gpt-3.5-turbo", openai_api_key=openai_api_key, temperature=0)

        # RetrievalQA 체인 생성
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": prompt_template}
        )

        # query 실행
        result = qa_chain({"query": query})
        st.success("완료!")
        st.text_area("답변", value=result['result'], height=900)
