import os
import openai
import pandas as pd
import json
from dotenv import load_dotenv
from .run_query import run_query, get_table_schema

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


#  SQL 생성 요청할 함수 스펙
# OpenAI Function Calling, 어떤 이름(name)의 함수를, 어떤 파라미터 구조(parameters) 로 호출할 수 있는지 정의해 주는 스펙
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

# 자연어 질문 -> SQL문 변경
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


# 해석 요청
def explain_df(df: pd.DataFrame) -> str:
    system_prompt = """
    당신은 데이터 분석 전문가입니다.
    아래 숫자형 데이터만 보고, 절대 컬럼명(헤더) 설명은 하지 마세요.
    1) 주요 수치(최댓값, 최솟값, 평균)
    2) 상위/하위 항목
    3) 눈에 띄는 패턴/이상치
    4) 이를 통한 인사이트 및 권장사항
    위 네 가지 항목으로 간결히 한국어로 분석해 주세요.
    """
    
    md_table = df.to_markdown(index=False)
    resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content":system_prompt},
            {"role": "user",   "content": md_table}
        ]
    )
    return resp.choices[0].message.content


# 질문 핸들러
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
