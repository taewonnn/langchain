import pandas as pd

# 노출/전환 비율
def add_performance_ratios(df: pd.DataFrame) -> pd.DataFrame:
    if "노출수" in df.columns and "클릭수" in df.columns:
        df["클릭률(%)"] = df.apply(
            lambda row: round((row["클릭수"] / row["노출수"] * 100), 1) if row["노출수"] > 0 else 0, axis=1
        )
    if "클릭수" in df.columns and "전환수" in df.columns:
        df["전환률(%)"] = df.apply(
            lambda row: round((row["전환수"] / row["클릭수"] * 100), 1) if row["클릭수"] > 0 else 0, axis=1
        )
    return df

# 컬럼 제외 / 숫자 포맷팅
def apply_comma_formatting(df: pd.DataFrame, exclude_columns: list = None) -> pd.DataFrame:
    if exclude_columns is None:
        exclude_columns = []
    for col in df.columns:
        if col in exclude_columns:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].apply(lambda x: f"{x:,}" if pd.notnull(x) else x)
    return df

#  합계 계산 / 추가
def append_totals_row(display_df: pd.DataFrame, original_df: pd.DataFrame, target_columns_mapping: dict, label_column: str = "idx", label_value: str = "합계") -> pd.DataFrame:
    total_row = {}
    for col in display_df.columns:
        if col in target_columns_mapping:
            orig_col = target_columns_mapping[col]
            if orig_col in original_df.columns:
                total_value = original_df[orig_col].sum()
                total_row[col] = f"{total_value:,}"
            else:
                total_row[col] = ""
        elif col == label_column:
            total_row[col] = label_value
        else:
            total_row[col] = ""
    return pd.concat([display_df, pd.DataFrame([total_row])], ignore_index=True)

def prepare_display_df(original_df: pd.DataFrame) -> pd.DataFrame:
    """
    원본 DataFrame에서 불필요한 컬럼을 제거하고, 컬럼명을 변경한 후,
    성과 비율(클릭률, 전환률) 계산, 숫자 포맷팅, 그리고 지정한 컬럼의 총합 행 추가를 순차적으로 처리합니다.
    """
    # 제거할 컬럼과 변경할 컬럼명 설정
    columns_to_exclude = ["adtypes", "teams_id", "manage_id", "bonus_click_sales"]
    custom_column_names = {
        "agency": "대행사",
        "id": "광고주 ID",
        "view_cnt": "노출수",
        "click_cnt": "클릭수",
        "click_sales": "비용",
        "order_cnt": "전환수",
        "order_price": "전환금액",
        "wdate_str": "일자"
    }
    target_columns_mapping = {
        "클릭수": "click_cnt",
        "전환수": "order_cnt",
        "전환금액": "order_price",
        "비용": "click_sales"
    }
    
    # 1. 불필요한 컬럼 제거 및 컬럼명 변경
    df_dropped = original_df.drop(columns=columns_to_exclude, errors="ignore")
    display_df = df_dropped.rename(columns=custom_column_names)
    
    # 2. 클릭률, 전환률 계산 추가
    display_df = add_performance_ratios(display_df)
    
    # 3. '일자' 컬럼은 제외하고 숫자형 데이터에 콤마 포맷팅 적용
    display_df = apply_comma_formatting(display_df, exclude_columns=['일자'])
    
    # 4. 지정된 4개 컬럼(클릭수, 전환수, 전환금액, 비용)의 총합 행 추가
    display_df = append_totals_row(display_df, df_dropped, target_columns_mapping, label_column="대행사", label_value="합계")
    
    return display_df
