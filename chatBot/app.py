import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from functions.run_query import run_query

load_dotenv()

# 세션 상태 초기화
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

st.set_page_config(layout="wide")
st.title("💬 ADN QnA ChatBot")

# 대화 기록 출력 - 역순)
st.subheader("📜 대화 기록")

for i, chat in enumerate(st.session_state.chat_history):
    st.markdown(f"**🙋‍♂️ 질문 {i+1}:** `{chat['question']}`")
    st.markdown(f"**🤖 답변:**\n\n{chat['answer']}", unsafe_allow_html=True)
    st.markdown("---")

# 👇 항상 하단에 위치하게 만들기 위한 구분선
st.markdown("## 📝 질문 입력")

# 하단에 고정된 느낌의 입력 영역 (가로 정렬)
col1, col2 = st.columns([0.85, 0.15])
with col1:
    query = st.text_input("질문을 입력하세요", key="query_input", label_visibility="collapsed")
with col2:
    ask_button = st.button("질문")

# 버튼 누르면 쿼리 실행 → 히스토리에 추가
if ask_button and query:
    try:
        result = run_query(query)
        df = pd.DataFrame(result)

        st.session_state.chat_history.append({
            "question": query,
            "answer": df.to_markdown(index=False) if not df.empty else "⚠️ 결과가 없습니다."
        })


    except Exception as e:
        st.session_state.chat_history.append({
            "question": query,
            "answer": f"❌ 오류: {e}"
        })

