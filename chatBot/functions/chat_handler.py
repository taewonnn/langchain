import os
import openai
import pandas as pd
import json
from dotenv import load_dotenv
from .run_query import run_query, get_table_schema

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


#  SQL 생성 요청할 함수 스펙
SQL_FUNCTION = {
    "name": "run_query",
    "description": "주어진 SQL을 실행하고 결과를 반환합니다.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "실행할 SQL 쿼리문"
            }
        },
        "required": ["query"]
    }
}


def nl_to_sql(nl_question: str) -> str:
    
    table = "adn_daily_agency_statics_2025"
    schema_info = get_table_schema(table)

    system_prompt = f"""
    당신은 SQL 전문가입니다.
    다음 테이블 스키마를 참고하여
    사용자의 질문을 가장 적절한 SQL로 작성해 주세요.

    테이블: {table}
    스키마: {schema_info}
    """

    # Function Calling 요청
    resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": nl_question}
        ],
        functions=[SQL_FUNCTION],
        function_call={"name": "run_query"}
    )
    
    args = json.loads(resp.choices[0].message.function_call.arguments)
    return args["query"]


def explain_df(df: pd.DataFrame) -> str:
    """
    DataFrame 결과를 Markdown으로 변환해
    OpenAI에 해석을 요청하고, 그 응답을 반환
    """
    md_table = df.to_markdown(index=False)
    resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "당신은 데이터 분석가입니다. 아래 테이블을 자세하게 한국어로 해석해주세요. 스키마는 굳이 해석할 필요는 없습니다."},
            {"role": "user",   "content": md_table}
        ]
    )
    return resp.choices[0].message.content


def handle_question(nl_question: str):
    """
    1) 자연어 → SQL 생성
    2) SQL 실행 → DataFrame 반환
    3) DataFrame 해석 → 설명 문자열 반환
    """
    sql = nl_to_sql(nl_question)      # SQL 생성
    rows = run_query(sql)             # DB에서 실행
    df = pd.DataFrame(rows)           # DataFrame 변환
    explanation = explain_df(df)      # 결과 해석
    return sql, df, explanation
