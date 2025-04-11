import os
import openai
import pandas as pd
import json
from dotenv import load_dotenv
from .run_query import run_query, get_table_schema

# 환경변수 로드 및 OpenAI API 키 설정
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Function Calling 스펙
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


# 질문 분류(DB / 일반)
def classify_question(nl_question: str) -> str:
    classification_prompt = f"""
    다음 질문이 데이터베이스(SQL)로부터 특정 값을 조회하거나,
    특정 테이블의 집계, 통계, 지표(예: 노출수, CTR, 전환수 등)를
    SELECT 쿼리로 얻어야 하는지 판단해 주세요.

    만약 SQL 쿼리가 필요해 보이면 'DB'라고,
    그 외에는 '일반'이라고만 짧게 답해 주세요.

    질문:
    {nl_question}
    """
    
    resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "당신은 질문 분류 전문가입니다."},
            {"role": "user", "content": classification_prompt},
        ]
    )
    classification = resp.choices[0].message.content.strip()
    return classification


# 일반 질문 처리
def handle_general_question(nl_question: str) -> str:
    """
    DB 관련이 아닌 일반 질문일 경우, GPT를 통해 단순 답변을 생성하고 반환합니다.
    
    Args:
        nl_question (str): 사용자가 입력한 일반 질문

    Returns:
        str: GPT가 생성한 답변 텍스트
    """
    resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "당신은 광고 분야의 질문에 대해 명확하고 유익한 답변을 제공할 수 있는 전문가입니다."},
            {"role": "user", "content": nl_question}
        ]
    )
    return resp.choices[0].message.content

# 자연어 질문 -> SQL 쿼리
def nl_to_sql(nl_question: str) -> str:
    # 대상 테이블명
    table = "adn_daily_agency_statics_2025"
    
    # 대상 테이블 스키마 정보
    schema_info = get_table_schema(table)

    system_prompt = f"""
    당신은 SQL 전문가입니다.
    다음 테이블 스키마를 참고하여
    사용자의 질문을 가장 적절한 SQL로 작성해 주세요.

    테이블: {table}
    스키마: {schema_info}
    """

    resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": nl_question}
        ],
        functions=[SQL_FUNCTION],
        function_call={"name": "run_query"}
    )

    args = json.loads(resp.choices[0].message.function_call.arguments)
    return args["query"]


# DataFrame 해석
def explain_df(df: pd.DataFrame) -> str:
    # 데이터 해석을 위한 시스템 프롬프트 구성
    system_prompt = """
    당신은 데이터 분석 전문가입니다.
    아래 숫자형 데이터만 보고, 절대 컬럼명(헤더) 설명은 하지 마세요.
    
    1) 주요 수치(최댓값, 최솟값, 평균)
    2) 상위/하위 항목
    3) 눈에 띄는 패턴/이상치
    4) 이를 통한 인사이트 및 권장사항
    
    위 네 가지 항목으로 간결히 한국어로 분석해 주세요.
    """
    
    # DataFrame -> 마크다운 테이블
    md_table = df.to_markdown(index=False)
    
    resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": md_table}
        ]
    )
    return resp.choices[0].message.content


# 질문 핸들러
def handle_question(nl_question: str):
    """
    사용자가 입력한 자연어 질문을 먼저 GPT를 통해 DB 관련 여부('DB' 또는 '일반')로 분류한 후,
    - DB 관련 질문일 경우:
        1) nl_to_sql() 함수를 통해 자연어 → SQL 쿼리문 생성
        2) run_query()를 통해 DB에서 SQL 실행 후 결과 DataFrame 변환
        3) explain_df()로 DataFrame 데이터 해석
    - 일반 질문일 경우:
        handle_general_question()을 통해 GPT로부터 일반 답변을 생성

    Args:
        nl_question (str): 사용자가 입력한 자연어 질문

    Returns:
        tuple: (sql, df, explanation)
            - DB 관련 질문인 경우, 생성된 SQL 쿼리, 실행 결과 DataFrame, 그리고 해석 결과를 포함합니다.
            - 일반 질문인 경우, sql과 df는 None으로 처리되고, 일반 답변 텍스트가 해석 결과에 포함됩니다.
    """
    # 질문 분류
    classification = classify_question(nl_question)
    
    if classification == "DB":
        # DB 관련 질문인 경우
        sql = nl_to_sql(nl_question)           # 자연어 -> SQL 변환
        rows = run_query(sql)                  # DB에서 SQL 실행
        df = pd.DataFrame(rows)                # 결과를 DataFrame으로 변환
        explanation = explain_df(df)           # DataFrame 데이터 해석 요청
        return sql, df, explanation
    else:
        # 일반 질문인 경우
        general_answer = handle_general_question(nl_question)
        return None, None, general_answer
