# app.py
import os
import streamlit as st
import pandas as pd
from streamlit.components.v1 import html

from dotenv import load_dotenv
from functions.chat_handler import handle_question

load_dotenv()
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(layout="wide")

# 세션 상태: messages 리스트로 통합
if "messages" not in st.session_state:
    st.session_state.messages = []

html(
    """
    <script>
        window.scrollTo(0, document.body.scrollHeight);
    </script>
    """,
    height=0,
)

# 대화 기록 출력
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])


# 입력창
if prompt := st.chat_input("질문을 입력하세요"):
    st.session_state.messages.append({"role":"user", "content": prompt})

    # SQL 생성 → 실행 → 해석
    try:
        sql, df, explanation = handle_question(prompt)
        # assistant 메시지 합성
        answer = (
            f"**💡 실행된 SQL:**\n```sql\n{sql}\n```\n\n"
            f"**📊 결과 테이블:**\n{df.to_markdown(index=False)}\n\n"
            f"**🔍 해석:**\n{explanation}"
        )
    except Exception as e:
        answer = f"❌ 오류: {e}"

    # 어시스턴트 메시지 저장 & 화면에 표시
    st.session_state.messages.append({"role":"assistant", "content": answer})
    st.chat_message("assistant").write(answer)
