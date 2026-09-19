"""
数据集划分脚本
按时间顺序划分训练集、验证集和测试集，避免数据泄露
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# 目录配置
DATA_PATH = Path(__file__).parent.parent.parent / 'result' / '特征工程' / '特征工程数据.csv'
OUTPUT_DIR = Path(__file__).parent.parent.parent / 'result' / '预测分析'
TRAIN_DIR = OUTPUT_DIR / '训练集'
VAL_DIR = OUTPUT_DIR / '验证集'
TEST_DIR = OUTPUT_DIR / '测试集'
TRAIN_DIR.mkdir(parents=True, exist_ok=True)
VAL_DIR.mkdir(parents=True, exist_ok=True)
TEST_DIR.mkdir(parents=True, exist_ok=True)

# 城市配置
TARGET_CITY = '兰州市'

# 划分比例：训练集 70%，验证集 10%，测试集 20%
TRAIN_RATIO = 0.7
VAL_RATIO = 0.1


def load_data():
    """加载特征工程后的数据"""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f'未找到文件: {DATA_PATH}')
    df = pd.read_csv(DATA_PATH)
    df['日期'] = pd.to_datetime(df['日期'])
    df = df.sort_values('日期').reset_index(drop=True)
    print(f'成功加载 {TARGET_CITY} 数据，共 {len(df)} 条记录')
    print(f'时间范围: {df["日期"].min().date()} ~ {df["日期"].max().date()}')
    return df


def split_data(df):
    """按时间顺序划分训练集、验证集和测试集"""
    train_end = int(len(df) * TRAIN_RATIO)
    val_end = int(len(df) * (TRAIN_RATIO + VAL_RATIO))
    
    train_df = df.iloc[:train_end].copy().reset_index(drop=True)
    val_df = df.iloc[train_end:val_end].copy().reset_index(drop=True)
    test_df = df.iloc[val_end:].copy().reset_index(drop=True)
    
    print(f'\n数据集划分:')
    print(f'  训练集: {len(train_df)} 条 ({TRAIN_RATIO:.0%})')
    print(f'    时间范围: {train_df["日期"].min().date()} ~ {train_df["日期"].max().date()}')
    print(f'  验证集: {len(val_df)} 条 ({VAL_RATIO:.0%})')
    print(f'    时间范围: {val_df["日期"].min().date()} ~ {val_df["日期"].max().date()}')
    print(f'  测试集: {len(test_df)} 条 ({1-TRAIN_RATIO-VAL_RATIO:.0%})')
    print(f'    时间范围: {test_df["日期"].min().date()} ~ {test_df["日期"].max().date()}')
    
    return train_df, val_df, test_df


def save_split_data(train_df, val_df, test_df):
    """保存划分后的数据"""
    # 保存训练集
    train_file = TRAIN_DIR / f'{TARGET_CITY}_train.csv'
    train_df.to_csv(train_file, index=False, encoding='utf-8-sig')
    print(f'\n训练集已保存: {train_file}')
    
    # 保存验证集
    val_file = VAL_DIR / f'{TARGET_CITY}_val.csv'
    val_df.to_csv(val_file, index=False, encoding='utf-8-sig')
    print(f'验证集已保存: {val_file}')
    
    # 保存测试集
    test_file = TEST_DIR / f'{TARGET_CITY}_test.csv'
    test_df.to_csv(test_file, index=False, encoding='utf-8-sig')
    print(f'测试集已保存: {test_file}')
    
    # 保存划分信息
    split_info = pd.DataFrame({
        '数据集': ['训练集', '验证集', '测试集'],
        '数据量': [len(train_df), len(val_df), len(test_df)],
        '占比': [f'{TRAIN_RATIO:.0%}', f'{VAL_RATIO:.0%}', f'{1-TRAIN_RATIO-VAL_RATIO:.0%}'],
        '开始日期': [train_df['日期'].min().date(), val_df['日期'].min().date(), test_df['日期'].min().date()],
        '结束日期': [train_df['日期'].max().date(), val_df['日期'].max().date(), test_df['日期'].max().date()]
    })
    info_file = OUTPUT_DIR / '数据集划分信息.csv'
    split_info.to_csv(info_file, index=False, encoding='utf-8-sig')
    print(f'划分信息已保存: {info_file}')


def save_statistics(train_df, val_df, test_df):
    """保存各数据集的统计信息"""
    numeric_cols = ['AQI', 'PM2.5', 'PM10', 'NO2', 'SO2', 'CO', 'O3']
    
    stats = []
    for name, df in [('训练集', train_df), ('验证集', val_df), ('测试集', test_df)]:
        for col in numeric_cols:
            stats.append({
                '数据集': name,
                '特征': col,
                '均值': round(df[col].mean(), 2),
                '标准差': round(df[col].std(), 2),
                '最小值': round(df[col].min(), 2),
                '最大值': round(df[col].max(), 2)
            })
    
    stats_df = pd.DataFrame(stats)
    stats_file = OUTPUT_DIR / '数据集统计信息.csv'
    stats_df.to_csv(stats_file, index=False, encoding='utf-8-sig')
    print(f'统计信息已保存: {stats_file}')


def main():
    print('=' * 60)
    print('数据集划分')
    print('=' * 60)
    
    # 1. 加载数据
    df = load_data()
    
    # 2. 划分数据
    print('\n' + '=' * 60)
    print('1. 划分训练集、验证集和测试集')
    print('=' * 60)
    train_df, val_df, test_df = split_data(df)
    
    # 3. 保存划分结果
    print('\n' + '=' * 60)
    print('2. 保存划分结果')
    print('=' * 60)
    save_split_data(train_df, val_df, test_df)
    
    # 4. 保存统计信息
    print('\n' + '=' * 60)
    print('3. 保存统计信息')
    print('=' * 60)
    save_statistics(train_df, val_df, test_df)
    
    print('\n' + '=' * 60)
    print(f'数据集划分完成！所有结果已保存至: {OUTPUT_DIR}')
    print('=' * 60)


if __name__ == '__main__':
    main()
