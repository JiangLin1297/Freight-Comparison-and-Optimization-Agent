"""公共数据清洗逻辑 - 供 CSVDataStore 和 init_db 共用

清洗行为与原 CSVDataStore._clean_data() 完全一致:
1. 去除列名和 Mode_DSC 字段的首尾空格
2. 数值字段转为 float (to_numeric, errors='coerce')
3. Service_Rating 缺失时填充 'C'
4. 删除含 NaN 的行
"""
import pandas as pd


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """清洗运价 DataFrame，返回清洗后的新 DataFrame"""
    df = df.copy()
    df.columns = df.columns.str.strip()

    df['Mode_DSC'] = df['Mode_DSC'].astype(str).str.strip()
    df['Min_Weight_Quant'] = pd.to_numeric(df['Min_Weight_Quant'], errors='coerce')
    df['Max_Weight_Quant'] = pd.to_numeric(df['Max_Weight_Quant'], errors='coerce')
    df['Min_Cost'] = pd.to_numeric(df['Min_Cost'], errors='coerce')
    df['Rate'] = pd.to_numeric(df['Rate'], errors='coerce')
    df['TPT_Day_Count'] = pd.to_numeric(df['TPT_Day_Count'], errors='coerce')

    if 'Service_Rating' in df.columns:
        df['Service_Rating'] = df['Service_Rating'].fillna('C').astype(str).str.strip()
    else:
        df['Service_Rating'] = 'C'

    df = df.dropna(subset=['Min_Weight_Quant', 'Max_Weight_Quant', 'Min_Cost', 'Rate', 'TPT_Day_Count'])
    return df
