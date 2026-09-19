"""
随机森林预测模型
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV, KFold
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, make_scorer
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

BASE_DIR = Path(__file__).parent.parent.parent / 'result' / '预测分析'
TRAIN_PATH = BASE_DIR / '训练集' / '兰州市_train.csv'
VAL_PATH = BASE_DIR / '验证集' / '兰州市_val.csv'
TEST_PATH = BASE_DIR / '测试集' / '兰州市_test.csv'
OUTPUT_DIR = BASE_DIR / '随机森林'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FEATURE_COLS = ['PM2.5', 'PM10', 'NO2', 'SO2', 'CO', 'O3', 'AQI_lag1', 'PM2.5_roll7_mean']
TARGET_COL = 'AQI'

# 超参数搜索区间
PARAM_GRID = {
    'n_estimators': [50, 100, 150, 200],
    'max_depth': [10, 15, 20, 25],
    'min_samples_split': [2, 5, 8]
}


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


def grid_search_tuning(X_train_val, y_train_val):
    """网格搜索寻优最优超参数，RMSE、MAE、R2三个指标"""
    print('\n' + '=' * 60)
    print('随机森林 超参数寻优（网格搜索 + 5折交叉验证）')
    print('=' * 60)

    model = RandomForestRegressor(random_state=42, n_jobs=-1)

    # 定义多个评分器
    def rmse_scorer(y_true, y_pred):
        return np.sqrt(mean_squared_error(y_true, y_pred))
    def mae_scorer(y_true, y_pred):
        return mean_absolute_error(y_true, y_pred)

    scoring = {
        'RMSE': make_scorer(rmse_scorer, greater_is_better=False),
        'MAE': make_scorer(mae_scorer, greater_is_better=False),
        'R2': 'r2'
    }

    # 5折交叉验证
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    grid_search = GridSearchCV(
        model, PARAM_GRID, cv=kf, scoring=scoring, refit='RMSE',
        n_jobs=-1, verbose=1, return_train_score=False
    )
    grid_search.fit(X_train_val, y_train_val)

    # 提取所有指标的结果
    results = pd.DataFrame()
    results['n_estimators'] = grid_search.cv_results_['param_n_estimators']
    results['max_depth'] = grid_search.cv_results_['param_max_depth']
    results['min_samples_split'] = grid_search.cv_results_['param_min_samples_split']
    results['RMSE'] = -grid_search.cv_results_['mean_test_RMSE']
    results['RMSE_std'] = grid_search.cv_results_['std_test_RMSE']
    results['MAE'] = -grid_search.cv_results_['mean_test_MAE']
    results['MAE_std'] = grid_search.cv_results_['std_test_MAE']
    results['R2'] = grid_search.cv_results_['mean_test_R2']
    results['R2_std'] = grid_search.cv_results_['std_test_R2']
    
    # 保存完整的网格搜索结果
    results.to_csv(OUTPUT_DIR / '网格搜索结果_完整.csv', index=False, encoding='utf-8-sig')
    print(f'\n网格搜索结果已保存: {OUTPUT_DIR / "网格搜索结果_完整.csv"}')

    # 找到各指标最优的参数组合
    best_rmse_idx = results['RMSE'].idxmin()
    best_mae_idx = results['MAE'].idxmin()
    best_r2_idx = results['R2'].idxmax()

    print(f'\n=== 最优参数汇总 ===')
    print(f'RMSE最优: RMSE={results.loc[best_rmse_idx, "RMSE"]:.4f}')
    print(f'  参数: n_estimators={results.loc[best_rmse_idx, "n_estimators"]}, '
          f'max_depth={results.loc[best_rmse_idx, "max_depth"]}, '
          f'min_samples_split={results.loc[best_rmse_idx, "min_samples_split"]}')
    print(f'MAE最优: MAE={results.loc[best_mae_idx, "MAE"]:.4f}')
    print(f'  参数: n_estimators={results.loc[best_mae_idx, "n_estimators"]}, '
          f'max_depth={results.loc[best_mae_idx, "max_depth"]}, '
          f'min_samples_split={results.loc[best_mae_idx, "min_samples_split"]}')
    print(f'R2最优: R2={results.loc[best_r2_idx, "R2"]:.4f}')
    print(f'  参数: n_estimators={results.loc[best_r2_idx, "n_estimators"]}, '
          f'max_depth={results.loc[best_r2_idx, "max_depth"]}, '
          f'min_samples_split={results.loc[best_r2_idx, "min_samples_split"]}')

    # 绘制参数寻优曲线（每个参数的三个指标都画）
    plot_tuning_curves(results)

    # 返回以RMSE为准的最优参数
    best_params = {
        'n_estimators': results.loc[best_rmse_idx, 'n_estimators'],
        'max_depth': results.loc[best_rmse_idx, 'max_depth'],
        'min_samples_split': results.loc[best_rmse_idx, 'min_samples_split']
    }
    return best_params, results.loc[best_rmse_idx, 'RMSE']


def plot_tuning_curves(results):
    """绘制超参数寻优曲线"""
    params = ['n_estimators', 'max_depth', 'min_samples_split']
    
    # 准备所有参数的数据
    all_data = {}
    for param in params:
        param_values = results[param].unique()
        param_values = sorted([v for v in param_values], key=lambda x: float(x))
        
        mean_rmse = [results[results[param] == v]['RMSE'].mean() for v in param_values]
        std_rmse = [results[results[param] == v]['RMSE_std'].mean() for v in param_values]
        mean_mae = [results[results[param] == v]['MAE'].mean() for v in param_values]
        std_mae = [results[results[param] == v]['MAE_std'].mean() for v in param_values]
        mean_r2 = [results[results[param] == v]['R2'].mean() for v in param_values]
        std_r2 = [results[results[param] == v]['R2_std'].mean() for v in param_values]
        
        all_data[param] = {
            'values': param_values,
            'rmse': (mean_rmse, std_rmse),
            'mae': (mean_mae, std_mae),
            'r2': (mean_r2, std_r2)
        }
    
    # ========== 图1: 3x3 子图网格 - 每个参数的三个指标分开显示 ==========
    fig, axes = plt.subplots(nrows=3, ncols=3, figsize=(20, 15))
    fig.suptitle('随机森林超参数寻优曲线（5折交叉验证）', fontsize=18, y=0.98)
    
    colors = {'RMSE': '#3b82f6', 'MAE': '#ef4444', 'R2': '#10b981'}
    
    for i, param in enumerate(params):
        data = all_data[param]
        x_values = [str(v) for v in data['values']]
        
        # RMSE (第1列)
        ax = axes[i, 0]
        ax.plot(x_values, data['rmse'][0], marker='o', linestyle='-', 
                color=colors['RMSE'], linewidth=2, markersize=6)
        ax.fill_between(x_values,
                       [m - s for m, s in zip(data['rmse'][0], data['rmse'][1])],
                       [m + s for m, s in zip(data['rmse'][0], data['rmse'][1])],
                       alpha=0.2, color=colors['RMSE'])
        ax.set_xlabel(param, fontsize=10)
        ax.set_ylabel('RMSE', fontsize=10, color=colors['RMSE'])
        ax.set_title(f'{param} - RMSE', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # MAE (第2列)
        ax = axes[i, 1]
        ax.plot(x_values, data['mae'][0], marker='s', linestyle='--', 
                color=colors['MAE'], linewidth=2, markersize=6)
        ax.fill_between(x_values,
                       [m - s for m, s in zip(data['mae'][0], data['mae'][1])],
                       [m + s for m, s in zip(data['mae'][0], data['mae'][1])],
                       alpha=0.2, color=colors['MAE'])
        ax.set_xlabel(param, fontsize=10)
        ax.set_ylabel('MAE', fontsize=10, color=colors['MAE'])
        ax.set_title(f'{param} - MAE', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # R2 (第3列)
        ax = axes[i, 2]
        ax.plot(x_values, data['r2'][0], marker='^', linestyle='-.', 
                color=colors['R2'], linewidth=2, markersize=6)
        ax.fill_between(x_values,
                       [m - s for m, s in zip(data['r2'][0], data['r2'][1])],
                       [m + s for m, s in zip(data['r2'][0], data['r2'][1])],
                       alpha=0.2, color=colors['R2'])
        ax.set_xlabel(param, fontsize=10)
        ax.set_ylabel('R2', fontsize=10, color=colors['R2'])
        ax.set_title(f'{param} - R2', fontsize=12)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout(rect=[0, 0.02, 1, 0.96])
    plt.savefig(OUTPUT_DIR / '超参数寻优综合图_3x3网格.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # ========== 图2: 每个参数的三个指标对比图（横向排列） ==========
    fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(24, 6))
    fig.suptitle('随机森林超参数寻优指标对比（5折交叉验证）', fontsize=18, y=0.98)
    
    for i, param in enumerate(params):
        data = all_data[param]
        x_values = [str(v) for v in data['values']]
        
        ax = axes[i]
        ax.plot(x_values, data['rmse'][0], marker='o', linestyle='-', 
                color=colors['RMSE'], linewidth=2, markersize=6, label='RMSE')
        ax.plot(x_values, data['mae'][0], marker='s', linestyle='--', 
                color=colors['MAE'], linewidth=2, markersize=6, label='MAE')
        
        ax2 = ax.twinx()
        ax2.plot(x_values, data['r2'][0], marker='^', linestyle='-.', 
                 color=colors['R2'], linewidth=2, markersize=6, label='R2')
        
        ax.set_xlabel(param, fontsize=12)
        ax.set_ylabel('RMSE / MAE', fontsize=12, color='#64748b')
        ax2.set_ylabel('R2', fontsize=12, color=colors['R2'])
        ax.set_title(f'{param} 参数寻优', fontsize=14)
        ax.legend(loc='upper left')
        ax2.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout(rect=[0, 0.02, 1, 0.96])
    plt.savefig(OUTPUT_DIR / '超参数寻优综合图_指标对比.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f'\n参数寻优综合图已保存至: {OUTPUT_DIR}')


def train_model(X_train, y_train, best_params=None):
    if best_params:
        model = RandomForestRegressor(**best_params, random_state=42, n_jobs=-1)
    else:
        model = RandomForestRegressor(n_estimators=150, max_depth=20, random_state=42,
                                      n_jobs=-1, min_samples_split=5)
    model.fit(X_train, y_train)
    print(f'\n模型参数: {best_params if best_params else "n_estimators=150, max_depth=20"}')
    return model


def evaluate_model(model, X, y_true):
    y_pred = model.predict(X)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    return y_pred, rmse, mae, r2


def save_results(y_true, y_pred, dates, metrics, best_params):
    results = pd.DataFrame({
        '日期': dates,
        '实际AQI': y_true,
        '预测AQI': np.round(y_pred, 2),
        '残差': np.round(y_true - y_pred, 2)
    })
    results.to_csv(OUTPUT_DIR / '预测结果.csv', index=False, encoding='utf-8-sig')

    # 保存评估指标（不含最优参数）
    metrics_df = pd.DataFrame([{
        '模型': metrics['模型'],
        'CV_RMSE': metrics['CV_RMSE'],
        'RMSE': metrics['RMSE'],
        'MAE': metrics['MAE'],
        'R2': metrics['R2']
    }])
    metrics_df.to_csv(OUTPUT_DIR / '评估指标.csv', index=False, encoding='utf-8-sig')

    # 保存最优参数
    params_df = pd.DataFrame([best_params])
    params_df.to_csv(OUTPUT_DIR / '最优参数.csv', index=False, encoding='utf-8-sig')


def plot_results(y_true, y_pred, dates, residuals, model):
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(dates, y_true, label='实际AQI', color='#3b82f6', alpha=0.8, linewidth=1)
    ax.plot(dates, y_pred, label='预测AQI', color='#ef4444', alpha=0.8, linewidth=1)
    ax.set_xlabel('日期', fontsize=12)
    ax.set_ylabel('AQI', fontsize=12)
    ax.set_title('随机森林: 实际AQI vs 预测AQI', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / '实际vs预测.png', dpi=300, bbox_inches='tight')
    plt.close()

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.scatter(dates, residuals, alpha=0.5, s=10, c='#64748b')
    ax.axhline(y=0, color='#ef4444', linestyle='--', linewidth=1)
    ax.set_xlabel('日期', fontsize=12)
    ax.set_ylabel('残差', fontsize=12)
    ax.set_title('随机森林: 残差分析', fontsize=14)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / '残差分析.png', dpi=300, bbox_inches='tight')
    plt.close()

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(y_true, y_pred, alpha=0.3, s=15, c='#3b82f6')
    min_val, max_val = min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max())
    ax.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='理想拟合线')
    ax.set_xlabel('实际AQI', fontsize=12)
    ax.set_ylabel('预测AQI', fontsize=12)
    ax.set_title('随机森林: 实际值 vs 预测值散点图', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / '拟合散点图.png', dpi=300, bbox_inches='tight')
    plt.close()

    importances = model.feature_importances_
    sorted_idx = np.argsort(importances)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh([FEATURE_COLS[i] for i in sorted_idx], importances[sorted_idx], color='#10b981')
    ax.set_xlabel('特征重要性', fontsize=12)
    ax.set_title('随机森林: 特征重要性', fontsize=14)
    ax.grid(True, alpha=0.3, axis='x')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / '特征重要性.png', dpi=300, bbox_inches='tight')
    plt.close()


def main():
    print('=' * 60)
    print('随机森林预测模型')
    print('=' * 60)

    train, val, test = load_data()
    X_train = train[FEATURE_COLS].values
    y_train = train[TARGET_COL].values
    X_val = val[FEATURE_COLS].values
    y_val = val[TARGET_COL].values
    X_test = test[FEATURE_COLS].values
    y_test = test[TARGET_COL].values
    dates = test['日期'].dt.strftime('%Y-%m-%d').values

    # 合并训练集和验证集用于网格搜索
    X_train_val = np.vstack([X_train, X_val])
    y_train_val = np.concatenate([y_train, y_val])

    # 超参数寻优
    best_params, cv_rmse = grid_search_tuning(X_train_val, y_train_val)

    # 使用最优参数训练模型
    print('\n使用最优参数训练模型...')
    model = train_model(X_train, y_train, best_params)

    print('\n验证集评估...')
    _, val_rmse, val_mae, val_r2 = evaluate_model(model, X_val, y_val)
    print(f'  RMSE: {val_rmse:.4f}, MAE: {val_mae:.4f}, R2: {val_r2:.4f}')

    print('\n测试集评估...')
    y_pred, test_rmse, test_mae, test_r2 = evaluate_model(model, X_test, y_test)
    print(f'  RMSE: {test_rmse:.4f}, MAE: {test_mae:.4f}, R2: {test_r2:.4f}')

    metrics = {
        '模型': '随机森林',
        'CV_RMSE': round(cv_rmse, 4),
        'RMSE': round(test_rmse, 4),
        'MAE': round(test_mae, 4),
        'R2': round(test_r2, 4),
        '最优参数': str(best_params)
    }

    residuals = y_test - y_pred
    save_results(y_test, y_pred, dates, metrics, best_params)
    plot_results(y_test, y_pred, pd.to_datetime(dates), residuals, model)

    print('\n随机森林预测完成！')


if __name__ == '__main__':
    main()
