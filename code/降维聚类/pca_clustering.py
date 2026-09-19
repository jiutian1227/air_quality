"""
PCA降维 + K-Means聚类脚本
使用特征工程后的数据进行降维和聚类分析
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import joblib
import json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# 目录配置
DATA_PATH = Path(__file__).parent.parent.parent / 'result' / '特征工程' / '特征工程数据.csv'
OUTPUT_DIR = Path(__file__).parent.parent.parent / 'result' / '降维聚类'
OUTPUT_IMAGE_DIR = OUTPUT_DIR / 'image'
OUTPUT_DATA_DIR = OUTPUT_DIR / '数据'
OUTPUT_MODEL_DIR = OUTPUT_DIR / 'model'
OUTPUT_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_MODEL_DIR.mkdir(parents=True, exist_ok=True)

# 城市配置
TARGET_CITY = '兰州市'


def load_data():
    """加载特征工程后的数据"""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f'未找到文件: {DATA_PATH}')
    df = pd.read_csv(DATA_PATH)
    df['日期'] = pd.to_datetime(df['日期'])
    print(f'成功加载 {TARGET_CITY} 数据，共 {len(df)} 条记录')
    return df


def prepare_clustering_features(df):
    """准备用于聚类的特征"""
    # 基础污染物特征
    cluster_features = ['PM2.5', 'PM10', 'NO2', 'SO2', 'CO', 'O3']
    
    # 加入衍生特征
    additional_features = ['AQI_lag1', 'PM2.5_roll7_mean']
    cluster_features += additional_features
    
    print(f'用于聚类的特征: {cluster_features}')
    print(f'聚类特征数量: {len(cluster_features)}')
    
    return df[cluster_features].copy()


def plot_elbow_method(X_scaled, city_name, max_k=10):
    """绘制肘部法则图，确定最佳聚类数"""
    inertias = []
    K = range(1, max_k + 1)
    
    for k in K:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(X_scaled)
        inertias.append(kmeans.inertia_)
    
    plt.figure(figsize=(10, 6))
    plt.plot(K, inertias, 'bo-', linewidth=2, markersize=8)
    plt.xlabel('聚类数量 (k)', fontsize=12)
    plt.ylabel('惯性 (Inertia)', fontsize=12)
    plt.title(f'{city_name} 肘部法则 - 确定最佳聚类数', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUTPUT_IMAGE_DIR / '肘部法则图.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 保存肘部法则数据
    elbow_df = pd.DataFrame({
        '聚类数量k': list(K),
        '惯性值': inertias
    })
    elbow_df.to_csv(OUTPUT_DATA_DIR / '肘部法则数据.csv', index=False, encoding='utf-8-sig')
    
    print('肘部法则图已保存')
    print(f'惯性值: {[round(x, 2) for x in inertias]}')
    return inertias


def perform_pca(X_scaled, n_components=2):
    """执行PCA降维"""
    pca = PCA(n_components=n_components, random_state=42)
    X_pca = pca.fit_transform(X_scaled)
    
    print(f'PCA降维完成，保留 {n_components} 个主成分')
    print(f'方差解释率: {pca.explained_variance_ratio_}')
    print(f'累计方差解释率: {sum(pca.explained_variance_ratio_):.2%}')
    
    # 保存方差解释率
    variance_df = pd.DataFrame({
        '主成分': [f'PC{i+1}' for i in range(n_components)],
        '方差解释率': pca.explained_variance_ratio_,
        '累计方差解释率': np.cumsum(pca.explained_variance_ratio_)
    })
    variance_df.to_csv(OUTPUT_DATA_DIR / 'PCA方差解释率.csv', index=False, encoding='utf-8-sig')
    
    return pca, X_pca


def perform_kmeans(X_pca, n_clusters=4):
    """执行K-Means聚类"""
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_pca)
    
    print(f'K-Means聚类完成，共 {n_clusters} 个聚类')
    return kmeans, clusters


def analyze_clusters(df, clusters, cluster_features, city_name):
    """分析每个聚类的特征"""
    df_analysis = df.copy()
    df_analysis['聚类'] = clusters
    
    # 计算每个聚类的统计特征
    cluster_stats = df_analysis.groupby('聚类')[cluster_features].mean().round(2)
    cluster_stats['样本数量'] = df_analysis['聚类'].value_counts().sort_index()
    cluster_stats['占比(%)'] = (cluster_stats['样本数量'] / len(df_analysis) * 100).round(2)
    
    # 重新排列列顺序
    cols = ['样本数量', '占比(%)'] + cluster_features
    cluster_stats = cluster_stats[cols]
    
    cluster_stats.to_csv(OUTPUT_DATA_DIR / '聚类统计信息.csv', encoding='utf-8-sig')
    print('聚类统计信息已保存')
    print(cluster_stats.to_string())
    
    return df_analysis, cluster_stats


def name_clusters(cluster_stats):
    """根据特征给聚类命名"""
    cluster_names = []
    for i in range(len(cluster_stats)):
        row = cluster_stats.iloc[i]
        pm25 = row['PM2.5']
        pm10 = row['PM10']
        so2 = row['SO2']

        if pm25 > 75 or pm10 > 150:
            if so2 > 50:
                name = f'聚类{i+1}: 燃煤型污染'
            else:
                name = f'聚类{i+1}: 沙尘型污染'
        elif pm25 > 35 or pm10 > 70:
            name = f'聚类{i+1}: 轻度污染'
        else:
            name = f'聚类{i+1}: 优良天气'
        cluster_names.append(name)

    return cluster_names


def plot_clusters_2d(X_pca, clusters, cluster_names, city_name):
    """绘制2D聚类散点图"""
    plt.figure(figsize=(12, 8))
    
    colors = plt.cm.Set3(np.linspace(0, 1, len(np.unique(clusters))))
    
    for i, color in enumerate(colors):
        mask = clusters == i
        plt.scatter(X_pca[mask, 0], X_pca[mask, 1], 
                   c=[color], label=cluster_names[i], 
                   alpha=0.6, s=30)
    
    plt.xlabel('主成分 1 (PC1)', fontsize=12)
    plt.ylabel('主成分 2 (PC2)', fontsize=12)
    plt.title(f'{city_name} PCA降维后K-Means聚类结果 (2D)', fontsize=14)
    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUTPUT_IMAGE_DIR / '聚类散点图2D.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print('2D聚类散点图已保存')


def plot_cluster_comparison(df_analysis, cluster_features, city_name):
    """绘制各聚类特征对比雷达图"""
    n_clusters = df_analysis['聚类'].nunique()
    
    # 标准化用于雷达图
    cluster_means = df_analysis.groupby('聚类')[cluster_features].mean()
    scaler = StandardScaler()
    cluster_means_scaled = pd.DataFrame(
        scaler.fit_transform(cluster_means),
        index=cluster_means.index,
        columns=cluster_means.columns
    )
    
    # 绘制雷达图
    fig = plt.figure(figsize=(12, 10))
    angles = np.linspace(0, 2 * np.pi, len(cluster_features), endpoint=False)
    
    for i in range(n_clusters):
        ax = fig.add_subplot(2, 2, i+1, polar=True)
        values = cluster_means_scaled.iloc[i].values
        values = np.concatenate((values, [values[0]]))
        angles_plot = np.concatenate((angles, [angles[0]]))
        
        ax.plot(angles_plot, values, 'o-', linewidth=2, label=f'聚类{i+1}')
        ax.fill(angles_plot, values, alpha=0.25)
        ax.set_xticks(angles)
        ax.set_xticklabels(cluster_features, fontsize=8)
        ax.set_title(f'聚类{i+1} 特征分布', fontsize=10)
        ax.grid(True)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_IMAGE_DIR / '聚类特征对比雷达图.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print('聚类特征对比雷达图已保存')


def plot_pca_variance(pca, city_name):
    """绘制PCA方差解释率柱状图"""
    fig, ax = plt.subplots(1, 2, figsize=(12, 5))
    
    # 左图：各主成分方差解释率
    ax[0].bar([f'PC{i+1}' for i in range(len(pca.explained_variance_ratio_))], 
              pca.explained_variance_ratio_, 
              color=['#1f77b4', '#ff7f0e'], 
              edgecolor='white', 
              linewidth=1)
    ax[0].set_xlabel('主成分', fontsize=12)
    ax[0].set_ylabel('方差解释率', fontsize=12)
    ax[0].set_title('各主成分方差解释率', fontsize=14)
    ax[0].grid(True, alpha=0.3)
    
    # 右图：累计方差解释率
    cumsum = np.cumsum(pca.explained_variance_ratio_)
    ax[1].bar([f'PC{i+1}' for i in range(len(cumsum))], 
              cumsum, 
              color=['#2ca02c', '#d62728'], 
              edgecolor='white', 
              linewidth=1)
    ax[1].set_xlabel('主成分', fontsize=12)
    ax[1].set_ylabel('累计方差解释率', fontsize=12)
    ax[1].set_title('累计方差解释率', fontsize=14)
    ax[1].grid(True, alpha=0.3)
    
    for i, v in enumerate(cumsum):
        ax[1].text(i, v + 0.01, f'{v:.2%}', ha='center', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_IMAGE_DIR / 'PCA方差解释率图.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print('PCA方差解释率图已保存')


def save_pca_results(df, X_pca, clusters, city_name):
    """保存PCA降维和聚类结果"""
    df_result = df.copy()
    df_result['PC1'] = X_pca[:, 0]
    df_result['PC2'] = X_pca[:, 1]
    df_result['聚类'] = clusters
    
    # 保存关键列
    save_cols = ['城市', '日期', 'AQI', '质量等级', 'PC1', 'PC2', '聚类'] + ['PM2.5', 'PM10', 'NO2', 'SO2', 'CO', 'O3']
    df_result = df_result[save_cols]
    
    df_result.to_csv(OUTPUT_DATA_DIR / 'PCA聚类结果.csv', index=False, encoding='utf-8-sig')
    print(f'PCA聚类结果已保存')
    return df_result


def save_models(scaler, pca, kmeans, cluster_names, cluster_features):
    """保存训练好的模型，供Web端调用预测"""
    joblib.dump(scaler, OUTPUT_MODEL_DIR / 'scaler.pkl')
    joblib.dump(pca, OUTPUT_MODEL_DIR / 'pca.pkl')
    joblib.dump(kmeans, OUTPUT_MODEL_DIR / 'kmeans.pkl')

    # 保存聚类元信息（特征顺序、聚类命名）
    meta = {
        'features': cluster_features,
        'cluster_names': cluster_names,
        'n_clusters': int(kmeans.n_clusters)
    }
    with open(OUTPUT_MODEL_DIR / 'cluster_meta.json', 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f'\n模型已保存至: {OUTPUT_MODEL_DIR}')


def main():
    print('=' * 60)
    print('PCA降维 + K-Means聚类')
    print('=' * 60)
    
    # 1. 加载数据
    df = load_data()
    
    # 2. 准备聚类特征
    print('\n' + '=' * 60)
    print('1. 准备聚类特征')
    print('=' * 60)
    X = prepare_clustering_features(df)
    
    # 3. 标准化数据
    print('\n' + '=' * 60)
    print('2. 标准化数据')
    print('=' * 60)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    print('数据标准化完成')
    
    # 4. 肘部法则确定最佳聚类数
    print('\n' + '=' * 60)
    print('3. 肘部法则确定聚类数')
    print('=' * 60)
    inertias = plot_elbow_method(X_scaled, TARGET_CITY, max_k=10)
    
    # 5. PCA降维到2D
    print('\n' + '=' * 60)
    print('4. PCA降维')
    print('=' * 60)
    pca, X_pca = perform_pca(X_scaled, n_components=2)
    
    # 6. 绘制PCA方差解释率图
    print('\n' + '=' * 60)
    print('5. 可视化PCA方差')
    print('=' * 60)
    plot_pca_variance(pca, TARGET_CITY)
    
    # 7. K-Means聚类（默认4类，可根据肘部法则调整）
    print('\n' + '=' * 60)
    print('6. K-Means聚类')
    print('=' * 60)
    n_clusters = 4
    kmeans, clusters = perform_kmeans(X_pca, n_clusters=n_clusters)
    
    # 8. 分析聚类
    print('\n' + '=' * 60)
    print('7. 聚类分析')
    print('=' * 60)
    df_analysis, cluster_stats = analyze_clusters(df, clusters, X.columns.tolist(), TARGET_CITY)
    cluster_names = name_clusters(cluster_stats)
    print(f'聚类命名: {cluster_names}')
    
    # 9. 可视化
    print('\n' + '=' * 60)
    print('8. 可视化')
    print('=' * 60)
    plot_clusters_2d(X_pca, clusters, cluster_names, TARGET_CITY)
    plot_cluster_comparison(df_analysis, X.columns.tolist()[:6], TARGET_CITY)
    
    # 10. 保存结果
    print('\n' + '=' * 60)
    print('9. 保存结果')
    print('=' * 60)
    save_pca_results(df, X_pca, clusters, TARGET_CITY)
    
    # 11. 保存模型供Web端预测
    print('\n' + '=' * 60)
    print('10. 保存模型')
    print('=' * 60)
    save_models(scaler, pca, kmeans, cluster_names, X.columns.tolist())
    
    print('\n' + '=' * 60)
    print(f'PCA降维和K-Means聚类完成！所有结果已保存至: {OUTPUT_DIR}')
    print('=' * 60)


if __name__ == '__main__':
    main()
