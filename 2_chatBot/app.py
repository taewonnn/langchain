import os
import streamlit as st
import pandas as pd
from streamlit.components.v1 import html

from dotenv import load_dotenv
from functions.chat_handler import handle_question
# run_query.py 내의 run_query 함수는 이미 두 DB의 fully qualified 이름을 사용하는 조인 쿼리를 실행하도록 구성되어 있음

# env 로드 및 OPENAI API KEY 설정
load_dotenv()
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")

# 페이지 레이아웃과 타이틀 설정
st.set_page_config(layout="wide")
st.title('ADN DB - QnA with Run_Query Integration')

# 대화 기록 저장 (세션 스테이트에 messages 리스트 사용)
if "messages" not in st.session_state:
    st.session_state.messages = []

# 사용자의 질문 입력창 (chat_input 사용)
prompt = st.chat_input("질문을 입력하세요")

if prompt:
    # 사용자가 입력한 질문을 세션 기록에 저장 (역할: user)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # handle_question 함수 호출:
    # - 자연어 질문을 받아 SQL 쿼리로 변환 (nl_to_sql 함수 내부에서 run_query 함수도 호출됨)
    # - 생성된 SQL 쿼리를 실행하여 결과 DataFrame과 해석을 반환함
    try:
        sql, df, explanation = handle_question(prompt, st.session_state.messages)
        
        # 결과가 DataFrame 형태로 존재하면, 실행된 SQL, 결과 테이블(마크다운 표시), 해석을 조합
        if df is not None:
            answer = (
                f"**💡 실행된 SQL:**\n```sql\n{sql}\n```\n\n"
                f"**📊 결과 테이블:**\n{df.to_markdown(index=False)}\n\n"
                f"**🔍 해석:**\n{explanation}"
            )
        else:
            answer = f"**🔍 답변:**\n{explanation}"
        
    except Exception as e:
        # 예외 발생 시 오류 메시지 표시
        answer = f"❌ 오류: {e}"

    # 어시스턴트의 응답(실행 결과 및 해석)을 세션 기록에 저장 (역할: assistant)
    st.session_state.messages.append({"role": "assistant", "content": answer})

# 저장된 대화 기록을 순서대로 화면에 출력
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])
