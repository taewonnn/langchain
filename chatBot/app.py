import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from functions.chat_handler import handle_question

load_dotenv()
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")

# 세션 상태 초기화
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

st.set_page_config(layout="wide")
st.title("💬 ADN QnA ChatBot")

# 대화 기록 출력
st.subheader("📜 대화 기록")
for i, chat in enumerate(st.session_state.chat_history):
    st.markdown(f"**🙋‍♂️ 질문 {i+1}:** `{chat['question']}`")
    st.markdown(f"**🤖 답변:**\n\n{chat['answer']}", unsafe_allow_html=True)
    st.markdown("---")

# 질문 입력 UI
st.markdown("## 📝 질문 입력")
col1, col2 = st.columns([0.85, 0.15])
with col1:
    query = st.text_input("질문을 입력하세요", key="query_input", label_visibility="collapsed")
with col2:
    ask_button = st.button("질문")

# 질문 처리
if ask_button and query:
    try:
        # 분리된 함수에서 한 번에 처리
        sql, df, explanation = handle_question(query)

        # 실행된 SQL 표시
        st.markdown("**💡 실행된 SQL:**")
        st.code(sql, language="sql")

        # 결과 테이블 표시
        st.dataframe(df)

        # 해석 결과 표시
        st.markdown("**🔍 해석:**")
        st.markdown(explanation)

        # 히스토리에 추가
        st.session_state.chat_history.append({
            "question": query,
            "answer": (
                f"**실행된 SQL:**\n```sql\n{sql}\n```\n\n"
                f"**결과 표:**\n{df.to_markdown(index=False)}\n\n"
                f"**해석:**\n{explanation}"
            )
        })

    except Exception as e:
        st.session_state.chat_history.append({
            "question": query,
            "answer": f"❌ 오류: {e}"
        })
