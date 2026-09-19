"""
线性回归预测模型
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
import json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# 目录配置
BASE_DIR = Path(__file__).parent.parent.parent / 'result' / '预测分析'
TRAIN_PATH = BASE_DIR / '训练集' / '兰州市_train.csv'
VAL_PATH = BASE_DIR / '验证集' / '兰州市_val.csv'
TEST_PATH = BASE_DIR / '测试集' / '兰州市_test.csv'
OUTPUT_DIR = BASE_DIR / '线性回归'
OUTPUT_MODEL_DIR = OUTPUT_DIR / 'model'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_MODEL_DIR.mkdir(parents=True, exist_ok=True)

FEATURE_COLS = ['PM2.5', 'PM10', 'NO2', 'SO2', 'CO', 'O3', 'AQI_lag1', 'PM2.5_roll7_mean']
TARGET_COL = 'AQI'


def load_data():
    train = pd.read_csv(TRAIN_PATH)
    train['日期'] = pd.to_datetime(train['日期'])
    val = pd.read_csv(VAL_PATH)
    val['日期'] = pd.to_datetime(val['日期'])
    test = pd.read_csv(TEST_PATH)
    test['日期'] = pd.to_datetime(test['日期'])
    print(f'训练集: {len(train)} 条')
    print(f'验证集: {len(val)} 条')
    print(f'测试集: {len(test)} 条')
    return train, val, test


def train_model(X_train, y_train):
    model = LinearRegression()
    model.fit(X_train, y_train)
    print(f'\n模型系数:')
    for feat, coef in zip(FEATURE_COLS, model.coef_):
        print(f'  {feat}: {coef:.4f}')
    print(f'截距: {model.intercept_:.4f}')
    return model


def evaluate_model(model, X, y_true):
    y_pred = model.predict(X)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    return y_pred, rmse, mae, r2


def save_results(y_true, y_pred, dates, metrics):
    # 保存预测结果
    results = pd.DataFrame({
        '日期': dates,
        '实际AQI': y_true,
        '预测AQI': np.round(y_pred, 2),
        '残差': np.round(y_true - y_pred, 2)
    })
    results.to_csv(OUTPUT_DIR / '预测结果.csv', index=False, encoding='utf-8-sig')
    print(f'\n预测结果已保存')

    # 保存评估指标
    metrics_df = pd.DataFrame([metrics])
    metrics_df.to_csv(OUTPUT_DIR / '评估指标.csv', index=False, encoding='utf-8-sig')
    print(f'评估指标已保存')


def plot_results(y_true, y_pred, dates, residuals, model):
    # 1. 实际值 vs 预测值对比图
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(dates, y_true, label='实际AQI', color='#3b82f6', alpha=0.8, linewidth=1)
    ax.plot(dates, y_pred, label='预测AQI', color='#ef4444', alpha=0.8, linewidth=1)
    ax.set_xlabel('日期', fontsize=12)
    ax.set_ylabel('AQI', fontsize=12)
    ax.set_title('线性回归: 实际AQI vs 预测AQI', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / '实际vs预测.png', dpi=300, bbox_inches='tight')
    plt.close()
    print('实际vs预测图已保存')

    # 2. 残差图
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.scatter(dates, residuals, alpha=0.5, s=10, c='#64748b')
    ax.axhline(y=0, color='#ef4444', linestyle='--', linewidth=1)
    ax.set_xlabel('日期', fontsize=12)
    ax.set_ylabel('残差', fontsize=12)
    ax.set_title('线性回归: 残差分析', fontsize=14)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / '残差分析.png', dpi=300, bbox_inches='tight')
    plt.close()
    print('残差分析图已保存')

    # 3. 散点拟合图
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(y_true, y_pred, alpha=0.3, s=15, c='#3b82f6')
    min_val = min(y_true.min(), y_pred.min())
    max_val = max(y_true.max(), y_pred.max())
    ax.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='理想拟合线')
    ax.set_xlabel('实际AQI', fontsize=12)
    ax.set_ylabel('预测AQI', fontsize=12)
    ax.set_title('线性回归: 实际值 vs 预测值散点图', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / '拟合散点图.png', dpi=300, bbox_inches='tight')
    plt.close()
    print('拟合散点图已保存')

    # 4. 特征系数柱状图
    fig, ax = plt.subplots(figsize=(10, 5))
    sorted_idx = np.argsort(model.coef_)
    ax.barh([FEATURE_COLS[i] for i in sorted_idx], model.coef_[sorted_idx], color='#3b82f6')
    ax.set_xlabel('特征系数', fontsize=12)
    ax.set_title('线性回归: 特征系数', fontsize=14)
    ax.grid(True, alpha=0.3, axis='x')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / '特征系数.png', dpi=300, bbox_inches='tight')
    plt.close()
    print('特征系数图已保存')


def save_model(model):
    """保存训练好的线性回归模型"""
    joblib.dump(model, OUTPUT_MODEL_DIR / 'linear_regression.pkl')
    meta = {
        'features': FEATURE_COLS,
        'target': TARGET_COL,
        'coefficients': {f: float(c) for f, c in zip(FEATURE_COLS, model.coef_)},
        'intercept': float(model.intercept_)
    }
    with open(OUTPUT_MODEL_DIR / 'linear_regression_meta.json', 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f'模型已保存至: {OUTPUT_MODEL_DIR}')


def main():
    print('=' * 60)
    print('线性回归预测模型')
    print('=' * 60)

    # 1. 加载数据
    train, val, test = load_data()

    X_train = train[FEATURE_COLS].values
    y_train = train[TARGET_COL].values
    X_val = val[FEATURE_COLS].values
    y_val = val[TARGET_COL].values
    X_test = test[FEATURE_COLS].values
    y_test = test[TARGET_COL].values
    dates = test['日期'].dt.strftime('%Y-%m-%d').values

    # 2. 训练模型
    print('\n训练模型...')
    model = train_model(X_train, y_train)

    # 3. 评估
    print('\n验证集评估...')
    _, val_rmse, val_mae, val_r2 = evaluate_model(model, X_val, y_val)
    print(f'  RMSE: {val_rmse:.4f}')
    print(f'  MAE: {val_mae:.4f}')
    print(f'  R²: {val_r2:.4f}')

    print('\n测试集评估...')
    y_pred, test_rmse, test_mae, test_r2 = evaluate_model(model, X_test, y_test)
    print(f'  RMSE: {test_rmse:.4f}')
    print(f'  MAE: {test_mae:.4f}')
    print(f'  R²: {test_r2:.4f}')

    metrics = {'模型': '线性回归', 'RMSE': round(test_rmse, 4), 'MAE': round(test_mae, 4), 'R²': round(test_r2, 4)}

    # 4. 保存结果
    residuals = y_test - y_pred
    save_results(y_test, y_pred, dates, metrics)

    # 5. 可视化
    plot_results(y_test, y_pred, pd.to_datetime(dates), residuals, model)

    # 6. 保存模型供Web端预测
    save_model(model)

    print('\n线性回归预测完成！')


if __name__ == '__main__':
    main()
