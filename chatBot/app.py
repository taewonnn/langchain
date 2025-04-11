import os
import streamlit as st
import pandas as pd
from streamlit.components.v1 import html

from dotenv import load_dotenv
from functions.chat_handler import handle_question

# env
load_dotenv()
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")

# 타이틀 / 레이아웃
st.set_page_config(layout="wide")
st.title('ADN DB - QnA')

# 대화 기록 저장용
if "messages" not in st.session_state:
    st.session_state.messages = []

# 입력창
prompt = st.chat_input("질문을 입력하세요")

if prompt:
    # 사용자가 입력한 질문을 세션 메시지에 저장 (역할: user)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 입력받은 질문 -> SQL, 결과, 해석 (대화 기록 전달)
    try:
        sql, df, explanation = handle_question(prompt, st.session_state.messages)
        if df is not None:
            answer = (
                f"**💡 실행된 SQL:**\n```sql\n{sql}\n```\n\n"
                f"**📊 결과 테이블:**\n{df.to_markdown(index=False)}\n\n"
                f"**🔍 해석:**\n{explanation}"
            )
        else:
            answer = f"**🔍 답변:**\n{explanation}"
        
    except Exception as e:
        answer = f"❌ 오류: {e}"

    # 어시스턴트의 응답을 세션 메시지에 저장 (역할: assistant)
    st.session_state.messages.append({"role": "assistant", "content": answer})

# 대화 기록 출력
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])
