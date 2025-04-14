import os
import openai
import pandas as pd
import json
from dotenv import load_dotenv
from .run_query import run_query, get_table_schema
from datetime import datetime
from .common import prepare_display_df


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
    table = 'adn_daily_agency_statics_2025'
    schema_info = get_table_schema(table)
    
    system_prompt = f'''
    너는 SQL 전문가야.
    다음 테이블 스키마 참고해서 사용자의 질문을 가장 적절한 SQL로 작성해줘
    
    - id: 광고주의 ID (광고주마다 유니크한 식별자)
    - manage_id: 내부 운영용 매니저 ID (대행사 혹은 내부식별자)

    **단, 반드시 SELECT * FROM {table}를 사용해야 해.**

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
    
    print("GPT Function Call === nl -> SQL")
    print(res.choices[0].message.function_call)  # 쿼리 확인용
    
    ans = json.loads(res.choices[0].message.function_call.arguments)
    return ans['query']

# DataFrame 해석 함수
def explain_df(df: pd.DataFrame, history: list = None) -> str:
    system_prompt = """
        너는 데이터 분석 전문가이자 광고 성과 평가 전문가야.
        
        아래 테이블은 광고 플랫폼의 DA 광고 성과 데이터를 포함하고 있어.
        해당 데이터는 노출수, 클릭수, 비용, 전환수, 전환금액 등의 지표를 포함하며,
        이 지표들은 각각 광고의 효율과 사용자 반응, 그리고 수익성을 나타내.
        
        아래 숫자형 데이터만 참고하여, 다음 항목들을 상세하고 구체적으로 분석해줘:
        
        1. **주요 수치 해석:**  
        - 최댓값, 최솟값, 평균 등의 기본 통계 수치를 어떻게 해석할 수 있는지 설명해줘.
        - 각 지표가 광고 성과에 어떤 영향을 미치는지 의견을 제시해줘.
        
        2. **패턴 및 트렌드:**  
        - 기간(일자)별 주요 지표의 추세를 분석해, 특정 시점이나 요일에 성과가 어떻게 달라지는지 확인해줘.
        - 광고주나 대행사 별로 성과에 차이가 있다면 이를 비교 분석해줘.
        
        3. **이상치 및 변동 요인:**  
        - 특정 지표에서 비정상적인 값이나 급격한 변동이 있는 경우, 그 원인에 대해 추정해줘.
        - 이상치가 광고 성과 최적화에 어떤 영향을 미치는지 의견을 제시해줘.
        
        4. **개선 방안 및 권고사항:**  
        - 현재 데이터를 바탕으로 광고 성과를 향상시키기 위한 구체적인 개선 방안(예: 타겟 세분화, 랜딩페이지 개선, 예산 재배분 등)을 제시해줘.
        - 미래의 광고 전략 수립에 도움이 될 만한 인사이트도 포함해줘.
        
        분석 결과는 간결하지만 심도 있게, 한국어로 작성해줘.
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


# 메인 질문 핸들러 함수
def handle_question(nl_question: str, history: list = None):
    """
    사용자가 입력한 질문을 분류하여, DB 관련 질문인 경우 자연어를 SQL 쿼리로 변환한 후 실행한 결과와 해석을 반환합니다.
    일반 질문인 경우 일반 답변을 리턴
    
    Returns:
        tuple: (sql, df, explanation)
            - DB 관련 질문: 생성된 SQL, 실행 결과 표시용 DataFrame, 해석 결과
            - 일반 질문: sql, df는 None, 해석에 일반 답변 포함
    """
    classification = classify_question(nl_question, history)
    
    if classification == "DB":
        sql = nl_to_sql(nl_question, history)
        rows = run_query(sql)
        original_df = pd.DataFrame(rows)  # 원본 데이터
        explanation = explain_df(original_df, history)  # 원본 데이터 해석
        
        # 표시용 DataFrame 준비 (+ 데이터 전처리)
        display_df = prepare_display_df(original_df)
        
        return sql, display_df, explanation
    else:
        general_answer = handle_general_question(nl_question, history)
        return None, None, general_answer
