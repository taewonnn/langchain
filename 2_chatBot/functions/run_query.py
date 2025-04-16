import pymysql, os
from dotenv import load_dotenv

load_dotenv()
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME_LOGS = os.getenv('DB_NAME_LOGS')
DB_NAME_ADS = os.getenv('DB_NAME_ADS')  # adn_paper_info(매체)


# db 연결
def run_query(query: str, db_name: str = DB_NAME_LOGS) -> list[dict]:
    """
    db_name 파라미터에 따라 log / ads DB에 연결
    """
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        db=db_name,
        charset="utf8",
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()
    finally:
        conn.close()

def get_table_schema(table_name: str, db_name: str = DB_NAME_LOGS) -> str:
    """
    INFORMATION_SCHEMA에서 table_name의 컬럼 스키마를 조회.
    db_name 인자에 따라 스키마 조회 대상 DB 변경.
    """
    sql = f"""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{db_name}'
        AND TABLE_NAME = '{table_name}';
    """
    cols = run_query(sql, db_name)
    return ", ".join(f"{r['COLUMN_NAME']}({r['DATA_TYPE']})" for r in cols)
