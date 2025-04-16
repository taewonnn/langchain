import os
import streamlit as st
import pandas as pd
import openai


from dotenv import load_dotenv
from functions.chat_handler import handle_question

# env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# 타이틀 / 레이아웃
st.set_page_config(layout="wide")
st.title('ADN DB - QnA')


# 테이블 선택 탭
st.sidebar.title("📊 테이블 선택")

page = st.sidebar.radio(" ", ["통계 데이터", "소재 별 데이터"], label_visibility="hidden")


table_mapping = {
    "통계 데이터": ("adn_daily_agency_statics_2025", os.getenv("DB_NAME_LOGS")),
    "소재 별 데이터": ("adn_daily_users_modes_report_statics_2025", os.getenv("DB_NAME_LOGS")),
}

selected_table, selected_db = table_mapping[page]

# 대화 기록 저장용

# 2-1. 페이지별로 메시지 기록을 따로 관리
if "messages" not in st.session_state:
    st.session_state.messages = {}       

if page not in st.session_state.messages:
    st.session_state.messages[page] = []


# 입력창
prompt = st.chat_input(f"{page}에 대해 질문을 입력하세요")

if prompt:
    # 사용자가 입력한 질문을 세션 메시지에 저장 (역할: user)
    st.session_state.messages[page].append({"role": "user", "content": prompt})

    # 입력받은 질문 -> SQL, 결과, 해석 (대화 기록 전달)
    try:
        sql, df, explanation = handle_question(
            prompt,
            selected_table,
            selected_db,
            st.session_state.messages[page],
        )
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
    st.session_state.messages[page].append({
        "role": "assistant",
        "content": (
            f"**💡 실행된 SQL:**\n```sql\n{sql}\n```\n\n"
            + (df.to_markdown(index=False) if df is not None else "")
            + f"\n\n**🔍 해석:**\n{explanation}"
        )
    })

# 대화 기록 출력
if page in st.session_state.messages:
    for msg in st.session_state.messages[page]:
        st.chat_message(msg["role"]).write(msg["content"])