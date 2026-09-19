
"""
兰州市空气质量数据预处理
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# 文件路径配置
DATA_PATH = Path(__file__).parent.parent.parent / 'data' / '兰州市_2014-2026空气质量.csv'
OUTPUT_DIR = Path(__file__).parent.parent.parent / 'result' / '数据预处理'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def calculate_quality_grade(aqi):
    """根据AQI计算质量等级"""
    if aqi <= 50:
        return '优'
    elif aqi <= 100:
        return '良'
    elif aqi <= 150:
        return '轻度污染'
    elif aqi <= 200:
        return '中度污染'
    elif aqi <= 300:
        return '重度污染'
    else:
        return '严重污染'


def handle_missing_values(df):
    """处理缺失值 - 不删除数据，只填充"""
    df_clean = df.copy()

    # 数值列用中位数填充
    numeric_cols = ['AQI', 'PM2.5', 'PM10', 'NO2', 'SO2', 'CO', 'O3', 'AQI排名']

    for col in numeric_cols:
        if df_clean[col].isnull().sum() > 0:
            median_val = df_clean[col].median()
            df_clean[col].fillna(median_val, inplace=True)
            print(f"  {col}: 用中位数 {median_val} 填充")

    # 质量等级用众数填充
    if df_clean['质量等级'].isnull().sum() > 0:
        mode_val = df_clean['质量等级'].mode()[0]
        df_clean['质量等级'].fillna(mode_val, inplace=True)
        print(f"  质量等级: 用众数 '{mode_val}' 填充")

    # 日期格式检查 - 不删除，用前后日期填充
    df_clean['日期'] = pd.to_datetime(df_clean['日期'], errors='coerce')
    if df_clean['日期'].isnull().sum() > 0:
        print(f"  日期: 有 {df_clean['日期'].isnull().sum()} 个无效日期，用前向填充")
        df_clean['日期'] = df_clean['日期'].fillna(method='ffill').fillna(method='bfill')

    return df_clean


def handle_anomalies(df):
    """处理异常值 - 不删除数据，只替换"""
    df_clean = df.copy()

    # 普通污染物用IQR方法
    regular_cols = ['AQI', 'PM2.5', 'PM10', 'NO2', 'SO2', 'O3']
    for col in regular_cols:
        Q1 = df_clean[col].quantile(0.25)
        Q3 = df_clean[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        outliers_count = ((df_clean[col] < lower_bound) | (df_clean[col] > upper_bound)).sum()
        if outliers_count > 0:
            df_clean[col] = df_clean[col].clip(lower=lower_bound, upper=upper_bound)
            print(f"  {col}: 替换了 {outliers_count} 个异常值")

    # CO单独用业务上限 (50000μg/m³)
    CO_UPPER_LIMIT = 50000
    co_outliers = (df_clean['CO'] > CO_UPPER_LIMIT).sum()
    if co_outliers > 0:
        df_clean['CO'] = df_clean['CO'].clip(upper=CO_UPPER_LIMIT)
        print(f"  CO: 替换了 {co_outliers} 个超过业务上限({CO_UPPER_LIMIT})的值")

    # 负值检测 - 用0替换
    all_numeric = ['AQI', 'PM2.5', 'PM10', 'NO2', 'SO2', 'CO', 'O3']
    for col in all_numeric:
        negative_count = (df_clean[col] < 0).sum()
        if negative_count > 0:
            print(f"  {col}: 发现 {negative_count} 个负值，用0替换")
            df_clean[col] = df_clean[col].clip(lower=0)

    return df_clean


def data_consistency_check(df):
    """数据一致性检查与修复"""
    df_clean = df.copy()

    # 1. 自动修复 AQI 范围 (0-500)
    aqi_outliers = df_clean[(df_clean['AQI'] < 0) | (df_clean['AQI'] > 500)]
    if len(aqi_outliers) > 0:
        df_clean['AQI'] = df_clean['AQI'].clip(0, 500)
        print(f"  AQI范围: 修复 {len(aqi_outliers)} 条超出范围的数据")

    # 2. 自动修复 PM2.5 > PM10
    pm_inconsistent = df_clean[df_clean['PM2.5'] > df_clean['PM10']]
    if len(pm_inconsistent) > 0:
        df_clean.loc[df_clean['PM2.5'] > df_clean['PM10'], 'PM2.5'] = df_clean.loc[
            df_clean['PM2.5'] > df_clean['PM10'], 'PM10']
        print(f"  PM2.5 <= PM10: 修复 {len(pm_inconsistent)} 条逻辑错误")

    # 3. 根据 AQI 重新计算质量等级
    original_grades = df_clean['质量等级'].copy()
    df_clean['质量等级'] = df_clean['AQI'].apply(calculate_quality_grade)
    grade_changes = (original_grades != df_clean['质量等级']).sum()
    if grade_changes > 0:
        print(f"  质量等级: 重新计算 {grade_changes} 条不匹配数据")

    return df_clean


def preprocess_data():
    print('=' * 60)
    print('兰州市空气质量数据预处理')
    print('=' * 60)
    
    # 1. 加载原始数据
    print('\n1. 加载原始数据...')
    df = pd.read_csv(DATA_PATH)
    print(f"原始数据量: {len(df)}")
    print(f'原始数据列名: {list(df.columns)}')
    
    # 2. 数据检查
    print('\n2. 数据质量检查...')
    print(f"缺失值统计:\n{df.isnull().sum()}")
    print(f"重复值数量: {df.duplicated().sum()}")
    
    # 3. 数据清洗
    print('\n3. 开始数据清洗...')
    
    # 1. 缺失值处理
    df = handle_missing_values(df)
    
    # 2. 异常值处理
    df = handle_anomalies(df)
    
    # 3. 数据一致性检查与修复
    df = data_consistency_check(df)
    
    # 按日期排序
    df = df.sort_values('日期').reset_index(drop=True)
    
    # 4. 保存预处理后的数据
    output_file = OUTPUT_DIR / '兰州市_cleaned.csv'
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f'\n4. 预处理完成!')
    print(f'数据已保存至: {output_file}')
    print(f'最终数据形状: {df.shape}')
    print(f'最终数据列名: {list(df.columns)}')
    print(f'数据时间范围: {df["日期"].min()} 至 {df["日期"].max()}')
    
    # 显示数据前5行
    print('\n数据预览:')
    print(df.head())
    
    return df

if __name__ == '__main__':
    preprocess_data()
