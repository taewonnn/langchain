import os 
import openai
import pandas as pd
import json

from datetime import datetime
from dotenv import load_dotenv

from .run_query import run_query,get_table_schema, DB_NAME_ADS,DB_NAME_LOGS

# env
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


# DB / 일반 질문 분류 함수
def classify_question(nl_question: str, history: list = None) -> str:
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
    
    return res.choices[0].message.content.strip()


# 일반 질문 처리 함수
def handle_general_question(nl_question: str, history: list = None) -> str:
    messages = history.copy() if history is not None else []
    messages.append({
        'role': 'system',
        'content': '너는 거짓말을 하지 않고, 명확하고 유익한 답변을 제공할 수 있는 전문가야'
    })
    messages.append({'role': 'user', 'content': nl_question})
    
    res = openai.chat.completions.create(
        model='gpt-4o',
        messages=messages
    )
    
    return res.choices[0].message.content


# 자연어 질문 -> SQL 쿼리 변환 함수
def nl_to_sql(nl_question: str, history: list = None) -> str:
    table = 'adn_clicks_2025'
    table2 = 'adn_paper_info'
    schema_info = get_table_schema(table)
    
    # clicks 테이블 스키마 (logs DB)
    schema_clicks = get_table_schema('adn_clicks_2025', source='logs')
    # paper_info 테이블 스키마 (ads DB)
    schema_paper  = get_table_schema('adn_paper_info', source='ads')
    
    system_prompt = f"""
        아래 두 테이블을 항상 조인해서 사용합니다.

        1) {DB_NAME_LOGS}.adn_clicks_2025  
        스키마: {schema_clicks}  
        *날짜 필드는 반드시 `wdate_str` 컬럼을 사용하세요.*

        2) {DB_NAME_ADS}.adn_paper_info  
        스키마: {schema_paper}

        기본 FROM 절은 다음과 같습니다:
        FROM {DB_NAME_LOGS}.adn_clicks_2025 AS a
        LEFT JOIN {DB_NAME_ADS}.adn_paper_info AS p
        -- COLLATE를 이용해 두 컬럼의 collation을 통일합니다
        ON a.paper_code COLLATE utf8mb4_unicode_ci
            = p.paper_code COLLATE utf8mb4_unicode_ci

        자연어 질문을 SQL로 변환할 때,
        - **날짜 필터**는 `a.wdate_str BETWEEN '시작일' AND '종료일'` 으로,
        - **JOIN 조건**에는 반드시 `COLLATE utf8mb4_unicode_ci`를 포함해 주세요.
    """
    
    messages = history.copy() if history is not None else []
    messages.append({'role': 'system', 'content': system_prompt})
    messages.append({'role': 'user', 'content': nl_question})
    
    res = openai.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        functions=[SQL_FUNCTION],
        function_call={"name": "run_query"}
    )
    
    print("GPT Function Call === nl -> SQL")
    # print(res.choices[0].message.function_call.arguments)  # 쿼리 확인용
    ans = json.loads(res.choices[0].message.function_call.arguments)
    print(ans['query'])

    return ans['query']


def handle_question(nl_question: str, history: list = None):
    classification = classify_question(nl_question, history)
    
    if classification == "DB":
        sql = nl_to_sql(nl_question, history)
        rows = run_query(sql)
        df = pd.DataFrame(rows)  # DataFrame 변환

        explanation = (
            f"💡 실행된 SQL:\n```sql\n{sql}\n```\n"
            f"📊 총 {len(df)}개의 레코드가 반환되었습니다."
        )
        
        return sql, df, explanation
    else:
        general_answer = handle_general_question(nl_question, history)
        return None, None, general_answer

