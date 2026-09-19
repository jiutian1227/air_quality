"""
特征工程脚本
生成指定的特征集
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# 目录配置
DATA_PATH = Path(__file__).parent.parent.parent / 'result' / '数据预处理' / '兰州市_cleaned.csv'
OUTPUT_DIR = Path(__file__).parent.parent.parent / 'result' / '特征工程'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 城市配置
TARGET_CITY = '兰州市'

# 指定特征列表
ORIGINAL_FEATURES = ['AQI', 'PM2.5', 'PM10', 'NO2', 'SO2', 'CO', 'O3']
TIME_FEATURES = ['年份', '月份', '季节', '星期几', '是否周末']
DERIVED_FEATURES = ['AQI_lag1', 'PM2.5_roll7_mean']


def load_data():
    """加载清洗后的数据"""
    df = pd.read_csv(DATA_PATH)
    df['日期'] = pd.to_datetime(df['日期'])
    df = df.sort_values('日期').reset_index(drop=True)
    print(f'成功加载 {TARGET_CITY} 数据，共 {len(df)} 条记录')
    return df


def add_time_features(df):
    """添加时间维度特征"""
    df = df.copy()
    
    df['年份'] = df['日期'].dt.year
    df['月份'] = df['日期'].dt.month
    df['星期几'] = df['日期'].dt.dayofweek + 1
    
    df['是否周末'] = (df['星期几'] >= 6).astype(int)
    
    def get_season(month):
        if month in [3, 4, 5]:
            return '春季'
        elif month in [6, 7, 8]:
            return '夏季'
        elif month in [9, 10, 11]:
            return '秋季'
        else:
            return '冬季'
    
    df['季节'] = df['月份'].apply(get_season)
    
    print('时间维度特征已添加')
    return df


def add_derived_features(df):
    """添加时序衍生特征"""
    df = df.copy()
    
    df['AQI_lag1'] = df['AQI'].shift(1)
    
    df['PM2.5_roll7_mean'] = df['PM2.5'].rolling(window=7, min_periods=1).mean()
    
    print('时序衍生特征已添加')
    return df


def select_features(df):
    """选择最终需要的特征"""
    all_features = ['日期', '城市', '质量等级'] + ORIGINAL_FEATURES + TIME_FEATURES + DERIVED_FEATURES
    
    df_selected = df[all_features].copy()
    
    print(f'已选择特征: {all_features}')
    return df_selected


def save_feature_list(df):
    """保存特征列表"""
    feature_info = []
    
    for feature in ORIGINAL_FEATURES:
        feature_info.append({'特征名': feature, '类型': '原始监测特征', '说明': get_feature_description(feature)})
    
    for feature in TIME_FEATURES:
        feature_info.append({'特征名': feature, '类型': '时间维度特征', '说明': get_time_description(feature)})
    
    for feature in DERIVED_FEATURES:
        feature_info.append({'特征名': feature, '类型': '时序衍生特征', '说明': get_derived_description(feature)})
    
    feature_list = pd.DataFrame(feature_info)
    feature_list.to_csv(OUTPUT_DIR / '特征列表.csv', index=False, encoding='utf-8-sig')
    print(f'特征列表已保存: 特征列表.csv')
    return feature_list


def get_feature_description(feature):
    """获取原始特征描述"""
    descriptions = {
        'AQI': '空气质量指数，综合评判空气质量',
        'PM2.5': '细颗粒物浓度',
        'PM10': '可吸入颗粒物浓度',
        'NO2': '二氧化氮浓度',
        'SO2': '二氧化硫浓度',
        'CO': '一氧化碳浓度',
        'O3': '臭氧浓度'
    }
    return descriptions.get(feature, '')


def get_time_description(feature):
    """获取时间特征描述"""
    descriptions = {
        '年份': '数据所属年份，用于年度对比分析',
        '月份': '数据所属月份，体现月度污染规律',
        '季节': '划分春/夏/秋/冬，分析季节性差异',
        '星期几': '当日对应周内天数（周一至周日）',
        '是否周末': '区分工作日/周末，挖掘作息、车流带来的污染差异'
    }
    return descriptions.get(feature, '')


def get_derived_description(feature):
    """获取衍生特征描述"""
    descriptions = {
        'AQI_lag1': 'AQI滞后1期，即前一日AQI数值',
        'PM2.5_roll7_mean': 'PM2.5七日滑动平均值，当日及前6天PM2.5均值'
    }
    return descriptions.get(feature, '')


def save_feature_statistics(df):
    """保存特征统计信息"""
    numeric_cols = ORIGINAL_FEATURES + ['年份', '月份', '星期几', '是否周末']
    
    stats = []
    for col in numeric_cols:
        stats.append({
            '特征': col,
            '非空值数量': df[col].notna().sum(),
            '缺失值数量': df[col].isna().sum(),
            '均值': round(df[col].mean(), 2) if df[col].notna().any() else np.nan,
            '标准差': round(df[col].std(), 2) if df[col].notna().any() else np.nan,
            '最小值': round(df[col].min(), 2) if df[col].notna().any() else np.nan,
            '最大值': round(df[col].max(), 2) if df[col].notna().any() else np.nan
        })
    
    stats_df = pd.DataFrame(stats)
    stats_df.to_csv(OUTPUT_DIR / '特征统计信息.csv', index=False, encoding='utf-8-sig')
    print(f'特征统计信息已保存: 特征统计信息.csv')
    return stats_df


def main():
    print('=' * 60)
    print('特征工程')
    print('=' * 60)
    
    # 1. 加载数据
    df = load_data()
    
    # 2. 添加时间维度特征
    print('\n' + '=' * 60)
    print('1. 添加时间维度特征')
    print('=' * 60)
    df = add_time_features(df)
    
    # 3. 添加时序衍生特征
    print('\n' + '=' * 60)
    print('2. 添加时序衍生特征')
    print('=' * 60)
    df = add_derived_features(df)
    
    # 4. 选择指定特征
    print('\n' + '=' * 60)
    print('3. 选择特征')
    print('=' * 60)
    df = select_features(df)
    
    # 5. 处理缺失值（仅删除滞后特征产生的首行缺失）
    print('\n' + '=' * 60)
    print('4. 处理缺失值')
    print('=' * 60)
    original_len = len(df)
    df = df.dropna().reset_index(drop=True)
    print(f'删除前 {original_len} 条，删除后 {len(df)} 条')
    
    # 6. 保存特征工程后的数据
    print('\n' + '=' * 60)
    print('5. 保存结果')
    print('=' * 60)
    output_file = OUTPUT_DIR / '特征工程数据.csv'
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f'特征工程后的数据已保存: 特征工程数据.csv')
    
    # 7. 保存特征列表和统计
    save_feature_list(df)
    save_feature_statistics(df)
    
    print('\n' + '=' * 60)
    print(f'特征工程完成！所有结果已保存至: {OUTPUT_DIR}')
    print('=' * 60)
    print(f'\n生成的特征总数: {len(ORIGINAL_FEATURES) + len(TIME_FEATURES) + len(DERIVED_FEATURES)}')
    print(f'  - 原始监测特征: {len(ORIGINAL_FEATURES)} 个')
    print(f'  - 时间维度特征: {len(TIME_FEATURES)} 个')
    print(f'  - 时序衍生特征: {len(DERIVED_FEATURES)} 个')


if __name__ == '__main__':
    main()