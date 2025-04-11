import os
import openai
import pandas as pd
import json
from dotenv import load_dotenv
from .run_query import run_query,get_table_schema
from datetime import datetime


# 환경변수 로드 및 OpenAI API 키 설정
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

current_date = datetime.now().strftime("%Y-%m-%d")

# Function Calling 스펙
SQL_FUNCTION = {
    'name': 'run_query',
    'description': '주어진 SQL을 실행하고 결과를 반환해준다',
    'parameter': {
        'type': 'object',
        'properties': {
            'query': {
                'type': 'string',
                'description': 'SQL query'
            }
        },
        'required': ['query']
    }
}


# 문 분류 (DB / 일반)
def classify_question(nl_question: str, history: list = None) ->str:
    classification_prompt = f'''
    질문이 DB로부터 특정 값을 조회하거나,
    특정 테이블의 집계, 통계, 지표(예: 노출수, CTR, 전환수 등)를 SELECT 쿼리로 얻어야 하는지 판단해줘.
    
    만약 SQL 쿼리가 필요해 보이면 'DB'라고, 그 외에는 '일반'이라고만 대답해줘.
    
    질문:
    {nl_question}
    '''
    
    messages = history.copy() if history is not None else []
    messages.append({'role': 'system', 'content': '질문 분류만 해줘'})
    messages.append({'role': 'user', 'content': classification_prompt})
    
    res = openai.chat.completions.create(
        model='gpt-4o',
        messages=messages
    )
    
    # print(res.choices[0].message.content.strip())
    return res.choices[0].message.content.strip()
    
# test
# classify_question('2025년 4월 1일 ~ 3일 클릭수 높은 순 정렬 200개까지')


# 일반 질문 처리
def handle_general_question(nl_question: str, history: list = None) -> str:
    messages = history.copy() if history is not None else []
    messages.append({'role': 'system', 'content': '너는 거짓말을 하지 않고, 명확하고 유익한 답변을 제공할 수 있는 전문가야'})
    messages.append({'role': 'user', 'content': nl_question})
    
    res = openai.chat.completions.create(
        model='gpt-4o',
        messages= messages
    )

    # print 
    # print(res.choices[0].message.content)
    return res.choices[0].message.content

# test
# handle_general_question('Model Context Protocol에 대해 알려줘')


# 자연어 질문 -> SQL 쿼리
def nl_to_sql(nl_question: str, history: list = None) ->str:
    table = 'adn_daily_agency_statics_2025'
    schema_info = get_table_schema(table)
    
    system_prompt = f'''
    너는 SQL 전문가야.
    다음 테이블 스키마 참고해서 사용자의 질문을 가장 적절한 SQL로 작성해줘
    
    테이블: {table}
    스키마: {schema_info}
    '''
    
    messages = history.copy() if history is not None else []
    messages.append({'role': 'system', 'content': system_prompt})
    messages.append({'role': 'user', 'content': nl_question})

    res = openai.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        functions=[SQL_FUNCTION],
        function_call={"name": "run_query"}
    )
    
    # print(json.loads(res.choices[0].message.function_call.arguments))
    
    ans = json.loads(res.choices[0].message.function_call.arguments)
    return ans['query']

# test
# nl_to_sql('2025년 4월 1일 ~ 3일 클릭수 높은 순 정렬 10개')


# DataFrame 해석
def explain_df(df: pd.DataFrame, history: list = None) -> str:
    system_prompt = """
    너는 데이터 분석 전문가야
    아래 숫자형 데이터만 보고, 절대 컬럼명(헤더) 설명은 하지마
    
    1) 주요 수치(최댓값, 최솟값, 평균, CTR 등등)
    2) 상위 / 하위 항목
    3) 눈에 띄는 패턴 / 이상치
    4) 이를 통한 인사이트 및 권장사항
    
    위 네 가지 항목으로 간결히 한국어로 분석해줘
    """
    
    md_table = df.to_markdown(index=False)
    messages = history.copy() if history is not None else []
    messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": md_table})
    
    res = openai.chat.completions.create(
        model='gpt-4o',
        messages=messages
    )
    
    return res.choices[0].message.content


# 질문 핸들러
def handle_question(nl_question: str, history: list = None):
    """_summary_
    사용자가 입력한 질문을 먼저 GPT를 통해 DB 관련 여부('DB' 또는 '일반')로 분류
    - DB 관련 질문일 경우:
        1) nl_to_sql()을 통해 자연어 → SQL 쿼리문 생성
        2) run_query()로 DB에서 SQL 실행 후 결과 DataFrame 변환
        3) explain_df()로 DataFrame 데이터 해석
    - 일반 질문일 경우:
        handle_general_question()로 일반 답변을 생성

    Args:
        nl_question (str): 사용자가 입력한 자연어 질문
        history (list): 이전 대화 기록

    Returns:
        tuple: (sql, df, explanation)
            - DB 관련 질문: 생성된 SQL, 실행 결과 DataFrame, 해석 결과
            - 일반 질문: sql, df는 None, 해석에 일반 답변 포함
    """
    classification = classify_question(nl_question, history)
    
    if classification == "DB":
        sql = nl_to_sql(nl_question, history)
        rows = run_query(sql)
        df = pd.DataFrame(rows)
        explanation = explain_df(df, history)
        return sql, df, explanation
    else:
        general_answer = handle_general_question(nl_question, history)
        return None, None, general_answer
    