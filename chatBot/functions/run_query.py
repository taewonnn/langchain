import pymysql
import os
from dotenv import load_dotenv

load_dotenv()
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME_LOGS = os.getenv('DB_NAME_LOGS')

def run_query(query):
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            db=DB_NAME_LOGS,
            charset="utf8",
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
        conn.close()
        return result
    
    except Exception as e:
        print("Error:", e)
        raise e


def get_table_schema(table_name: str) -> str:
    """
    INFORMATION_SCHEMA에서 컬럼명과 타입을 조회해
    'col1(TYPE), col2(TYPE), ...' 형태의 문자열로 반환합니다.
    """
    sql = f"""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{DB_NAME_LOGS}'
        AND TABLE_NAME = '{table_name}';
    """
    cols = run_query(sql)
    return ", ".join(f"{row['COLUMN_NAME']}({row['DATA_TYPE']})" for row in cols)