import os
from dotenv import load_dotenv
import pandas as pd
from pprint import pprint

from langchain.chat_models import ChatOpenAI
from langchain.schema import Document
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')

# CSV 로드 (전체 데이터 사용)
df = pd.read_csv('/Users/taewonpark/github/langchain/keyword/data/log_keyword_20250307.csv')
keyword_list = df[['ui', 'ad_ids', 'k']].dropna()

# 각 행의 데이터를 Document로 변환 (문맥 정보를 풍부하게 포함)
documents = []
for _, row in keyword_list.iterrows():
    # 각 문서에 k 뿐만 아니라 ui, ad_ids 정보를 함께 포함하여 임베딩의 풍부함을 증가시킴
    content = f"키워드: {row['k']}\nUI: {row['ui']}\nad_ids: {row['ad_ids']}"
    metadata = {'ui': row['ui'], 'ad_ids': row['ad_ids'], 'k': row['k']}
    documents.append(Document(page_content=content, metadata=metadata))

# 임베딩 생성 및 FAISS 벡터 스토어 구축
embedding = OpenAIEmbeddings(openai_api_key=openai_api_key)
vectorstore = FAISS.from_documents(documents, embedding)

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

# Retriever 설정
retriever = vectorstore.as_retriever(search_kwargs={"k": 20})
llm = ChatOpenAI(model_name="gpt-3.5-turbo", openai_api_key=openai_api_key, temperature=0)

# RetrievalQA 체인 생성
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    chain_type_kwargs={"prompt": prompt_template}
)

# 질의 실행
query = "루즈핏 티셔츠"
result = qa_chain({"query": query})
pprint(result['result'])
