import pymysql
import os
from dotenv import load_dotenv
import pymysql.cursors

load_dotenv()
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME_LOGS = os.getenv('DB_NAME_LOGS')
DB_NAME_ADS = os.getenv('DB_NAME_ADS')

def run_query_logs(query):
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            db=DB_NAME_LOGS,
            charset='utf8mb4',
            init_command="SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci",
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
        conn.close()
        return result
    except Exception as e:
        print('Error (logs DB):', e)
        raise e

def run_query_ads(query):
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            db=DB_NAME_ADS,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
        conn.close()
        return result
    except Exception as e:
        print('Error (ads DB):', e)
        raise e


def run_query(query):
    """
    두 DB 조인 쿼리 실행을 위해, logs DB에 연결 후 쿼리 실행
    (쿼리에는 이미 {DB_NAME_ADS}와 {DB_NAME_LOGS}가 fully qualified name으로 포함되어 있음)
    """
    return run_query_logs(query)


def get_table_schema(table_name: str, source: str = 'logs') -> str:
    # source에 따라 사용할 데이터베이스와 연결 함수를 선택
    if source == 'logs':
        db_name = DB_NAME_LOGS
        run_query_func = run_query_logs
    elif source == 'ads':
        db_name = DB_NAME_ADS
        run_query_func = run_query_ads
    else:
        raise ValueError("source 인자는 'logs' 또는 'ads' 여야 합니다.")
    
    sql = f"""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{db_name}'
        AND TABLE_NAME = '{table_name}';
    """
    
    cols = run_query_func(sql)
    return ", ".join(f"{row['COLUMN_NAME']}({row['DATA_TYPE']})" for row in cols)
