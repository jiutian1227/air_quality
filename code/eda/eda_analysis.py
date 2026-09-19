
"""
EDA数据探索与可视化脚本
步骤一：数据探索与可视化
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# 目录配置
DATA_PATH = Path(__file__).parent.parent.parent / 'result' / '数据预处理' / '兰州市_cleaned.csv'
IMAGE_DIR = Path(__file__).parent.parent.parent / 'result' / 'eda' / 'image'
DATA_OUTPUT_DIR = Path(__file__).parent.parent.parent / 'result' / 'eda' / '数据'

# 创建目录
IMAGE_DIR.mkdir(parents=True, exist_ok=True)
DATA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 城市配置
TARGET_CITY = '兰州市'


def load_data():
    """加载清洗后的数据"""
    df = pd.read_csv(DATA_PATH)
    df['日期'] = pd.to_datetime(df['日期'])
    df = df.sort_values('日期').reset_index(drop=True)
    print(f'成功加载 {TARGET_CITY} 数据，共 {len(df)} 条记录')
    return df


def save_statistics(df):
    """生成并保存统计汇总表"""
    numeric_cols = ['AQI', 'PM2.5', 'PM10', 'NO2', 'SO2', 'CO', 'O3']
    
    stats = []
    for col in numeric_cols:
        stats.append({
            '特征': col,
            '均值': round(df[col].mean(), 2),
            '标准差': round(df[col].std(), 2),
            '最小值': round(df[col].min(), 2),
            '25%分位数': round(df[col].quantile(0.25), 2),
            '中位数': round(df[col].median(), 2),
            '75%分位数': round(df[col].quantile(0.75), 2),
            '最大值': round(df[col].max(), 2)
        })
    
    stats_df = pd.DataFrame(stats)
    stats_df.to_csv(DATA_OUTPUT_DIR / '统计汇总表.csv', index=False, encoding='utf-8-sig')
    print(f'统计汇总表已保存: 统计汇总表.csv')
    print(stats_df.to_string(index=False))
    return stats_df


def save_quality_distribution(df):
    """生成并保存质量等级分布表和饼图"""
    quality_order = ['优', '良', '轻度污染', '中度污染', '重度污染', '严重污染']
    dist_df = df['质量等级'].value_counts().reindex(quality_order).fillna(0).reset_index()
    dist_df.columns = ['质量等级', '数量']
    dist_df['占比(%)'] = round(dist_df['数量'] / len(df) * 100, 2)
    
    dist_df.to_csv(DATA_OUTPUT_DIR / '空气质量等级分布数据.csv', index=False, encoding='utf-8-sig')
    print(f'质量等级分布表已保存: 空气质量等级分布数据.csv')
    print(dist_df.to_string(index=False))
    
    # 绘制饼图
    plt.figure(figsize=(10, 8))
    colors = ['#2ecc71', '#3498db', '#f39c12', '#e67e22', '#e74c3c', '#8e44ad']
    plt.pie(dist_df['数量'], labels=dist_df['质量等级'], autopct='%1.1f%%', 
            colors=colors, startangle=90)
    plt.title(f'{TARGET_CITY} 空气质量等级分布')
    plt.savefig(IMAGE_DIR / '空气质量等级分布饼图.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f'空气质量等级分布饼图已保存')
    
    return dist_df


def plot_time_series(df):
    """绘制时间序列图"""
    # 1. AQI时间趋势
    plt.figure(figsize=(16, 6))
    plt.plot(df['日期'], df['AQI'], linewidth=0.8, alpha=0.7, label='AQI')
    plt.xlabel('日期')
    plt.ylabel('AQI')
    plt.title(f'{TARGET_CITY} AQI时间趋势')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(IMAGE_DIR / 'AQI时间趋势.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 保存AQI每日数据
    aqi_daily = df[['日期', 'AQI']].copy()
    aqi_daily.columns = ['日期', 'AQI指数']
    aqi_daily.to_csv(DATA_OUTPUT_DIR / 'AQI每日数据.csv', index=False, encoding='utf-8-sig')
    
    # 2. 各污染物时间趋势（子图）
    pollutants = ['PM2.5', 'PM10', 'NO2', 'SO2', 'CO', 'O3']
    fig, axes = plt.subplots(3, 2, figsize=(16, 12))
    axes = axes.flatten()
    
    for i, pollutant in enumerate(pollutants):
        axes[i].plot(df['日期'], df[pollutant], linewidth=0.6, alpha=0.7, color=plt.cm.Set2(i))
        axes[i].set_title(f'{pollutant} 时间趋势')
        axes[i].set_xlabel('日期')
        axes[i].set_ylabel(pollutant)
        axes[i].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(IMAGE_DIR / '污染物时间趋势.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 保存污染物每日数据
    pollutants_daily = df[['日期'] + pollutants].copy()
    pollutants_daily.to_csv(DATA_OUTPUT_DIR / '污染物每日数据.csv', index=False, encoding='utf-8-sig')
    
    print('时间序列图已保存')


def plot_monthly_average(df):
    """绘制月度平均AQI柱状图"""
    df['月份'] = df['日期'].dt.to_period('M')
    monthly_avg = df.groupby('月份')['AQI'].mean().reset_index()
    monthly_avg['月份'] = monthly_avg['月份'].astype(str)
    
    plt.figure(figsize=(14, 6))
    plt.bar(range(len(monthly_avg)), monthly_avg['AQI'], color='#3498db', alpha=0.7)
    plt.xlabel('月份')
    plt.ylabel('平均AQI')
    plt.title(f'{TARGET_CITY} 月度平均AQI')
    plt.xticks(range(len(monthly_avg))[::3], monthly_avg['月份'][::3], rotation=45)
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(IMAGE_DIR / '月度平均AQI.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 保存月度数据
    monthly_avg.to_csv(DATA_OUTPUT_DIR / '月度平均AQI数据.csv', index=False, encoding='utf-8-sig')
    print('月度平均AQI图和表格已保存')


def plot_seasonal_average(df):
    """绘制季度平均AQI柱状图"""
    def get_season(month):
        if month in [3, 4, 5]:
            return '春季'
        elif month in [6, 7, 8]:
            return '夏季'
        elif month in [9, 10, 11]:
            return '秋季'
        else:
            return '冬季'
    
    df['季节'] = df['日期'].dt.month.apply(get_season)
    season_order = ['春季', '夏季', '秋季', '冬季']
    seasonal_avg = df.groupby('季节')['AQI'].mean().reindex(season_order).reset_index()
    
    plt.figure(figsize=(10, 6))
    colors = ['#2ecc71', '#f1c40f', '#e67e22', '#3498db']
    plt.bar(seasonal_avg['季节'], seasonal_avg['AQI'], color=colors, alpha=0.7)
    plt.xlabel('季节')
    plt.ylabel('平均AQI')
    plt.title(f'{TARGET_CITY} 季度平均AQI')
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(IMAGE_DIR / '季度平均AQI.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 保存季度数据
    seasonal_avg.to_csv(DATA_OUTPUT_DIR / '季度平均AQI数据.csv', index=False, encoding='utf-8-sig')
    print('季度平均AQI图和表格已保存')


def save_correlation_matrix(df):
    """生成并保存相关性矩阵和热力图"""
    numeric_cols = ['AQI', 'PM2.5', 'PM10', 'NO2', 'SO2', 'CO', 'O3']
    corr_matrix = df[numeric_cols].corr()
    corr_matrix = corr_matrix.round(3)
    
    corr_matrix.to_csv(DATA_OUTPUT_DIR / '污染物相关性矩阵.csv', encoding='utf-8-sig')
    print(f'相关性矩阵已保存: 污染物相关性矩阵.csv')
    print(corr_matrix)
    
    # 绘制热力图
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, cmap='RdBu_r', center=0, 
                square=True, linewidths=1, cbar_kws={'shrink': 0.8})
    plt.title(f'{TARGET_CITY} 污染物相关性热力图')
    plt.tight_layout()
    plt.savefig(IMAGE_DIR / '污染物相关性热力图.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return corr_matrix


def plot_scatter_pairs(df):
    """绘制关键特征散点图"""
    # PM2.5 vs PM10
    plt.figure(figsize=(10, 6))
    plt.scatter(df['PM2.5'], df['PM10'], alpha=0.5, s=10)
    plt.xlabel('PM2.5')
    plt.ylabel('PM10')
    plt.title(f'{TARGET_CITY} PM2.5 vs PM10')
    plt.grid(True, alpha=0.3)
    plt.savefig(IMAGE_DIR / 'PM2.5与PM10散点图.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 保存PM2.5 vs PM10数据
    scatter_pm25_pm10 = df[['PM2.5', 'PM10']].copy()
    scatter_pm25_pm10.to_csv(DATA_OUTPUT_DIR / 'PM2.5与PM10散点数据.csv', index=False, encoding='utf-8-sig')
    
    # PM2.5 vs AQI
    plt.figure(figsize=(10, 6))
    plt.scatter(df['PM2.5'], df['AQI'], alpha=0.5, s=10, color='#e74c3c')
    plt.xlabel('PM2.5')
    plt.ylabel('AQI')
    plt.title(f'{TARGET_CITY} PM2.5 vs AQI')
    plt.grid(True, alpha=0.3)
    plt.savefig(IMAGE_DIR / 'PM2.5与AQI散点图.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 保存PM2.5 vs AQI数据
    scatter_pm25_aqi = df[['PM2.5', 'AQI']].copy()
    scatter_pm25_aqi.to_csv(DATA_OUTPUT_DIR / 'PM2.5与AQI散点数据.csv', index=False, encoding='utf-8-sig')
    
    print('散点图已保存')


def main():
    print('=' * 60)
    print('EDA数据探索与可视化')
    print('=' * 60)
    
    # 1. 加载数据
    df = load_data()
    
    # 2. 生成统计汇总表
    print('\n' + '=' * 60)
    print('1. 统计汇总')
    print('=' * 60)
    save_statistics(df)
    
    # 3. 质量等级分布
    print('\n' + '=' * 60)
    print('2. 质量等级分布')
    print('=' * 60)
    save_quality_distribution(df)
    
    # 4. 时间序列图
    print('\n' + '=' * 60)
    print('3. 时间序列分析')
    print('=' * 60)
    plot_time_series(df)
    plot_monthly_average(df)
    plot_seasonal_average(df)
    
    # 5. 相关性分析
    print('\n' + '=' * 60)
    print('4. 相关性分析')
    print('=' * 60)
    save_correlation_matrix(df)
    
    # 6. 散点图分析
    print('\n' + '=' * 60)
    print('5. 散点图分析')
    print('=' * 60)
    plot_scatter_pairs(df)
    
    print('\n' + '=' * 60)
    print(f'EDA分析完成！')
    print(f'图片已保存至: {IMAGE_DIR}')
    print(f'数据已保存至: {DATA_OUTPUT_DIR}')
    print('=' * 60)


if __name__ == '__main__':
    main()
