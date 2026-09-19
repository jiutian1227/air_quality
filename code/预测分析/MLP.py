"""
MLP预测模型
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, make_scorer
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

BASE_DIR = Path(__file__).parent.parent.parent / 'result' / '预测分析'
TRAIN_PATH = BASE_DIR / '训练集' / '兰州市_train.csv'
VAL_PATH = BASE_DIR / '验证集' / '兰州市_val.csv'
TEST_PATH = BASE_DIR / '测试集' / '兰州市_test.csv'
OUTPUT_DIR = BASE_DIR / 'MLP'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FEATURE_COLS = ['PM2.5', 'PM10', 'NO2', 'SO2', 'CO', 'O3', 'AQI_lag1', 'PM2.5_roll7_mean']
TARGET_COL = 'AQI'

# 超参数搜索区间
PARAM_GRID = {
    'hidden_units': [64, 128],
    'dropout_rate': [0.2, 0.3],
    'learning_rate': [0.01, 0.001]
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


def build_mlp_model(input_dim, hidden_units=128, dropout_rate=0.3, learning_rate=0.001):
    """构建MLP模型"""
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, Dropout
    from tensorflow.keras.optimizers import Adam

    model = Sequential([
        Dense(hidden_units, activation='relu', input_shape=(input_dim,)),
        Dropout(dropout_rate),
        Dense(hidden_units // 2, activation='relu'),
        Dropout(dropout_rate),
        Dense(hidden_units // 4, activation='relu'),
        Dropout(dropout_rate * 0.5),
        Dense(1)
    ])

    optimizer = Adam(learning_rate=learning_rate)
    model.compile(optimizer=optimizer, loss='mse')
    return model


def grid_search_tuning(X_train_val, y_train_val):
    """网格搜索寻优最优超参数，同时计算RMSE、MAE、R2三个指标"""
    print('\n' + '=' * 60)
    print('MLP 超参数寻优（网格搜索 + 5折交叉验证）')
    print('=' * 60)

    input_dim = X_train_val.shape[1]
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    # 存储所有组合的结果
    results = []

    for hidden_units in PARAM_GRID['hidden_units']:
        for dropout_rate in PARAM_GRID['dropout_rate']:
            for learning_rate in PARAM_GRID['learning_rate']:
                fold_scores = {'RMSE': [], 'MAE': [], 'R2': []}

                for train_idx, val_idx in kf.split(X_train_val):
                    X_train_fold, X_val_fold = X_train_val[train_idx], X_train_val[val_idx]
                    y_train_fold, y_val_fold = y_train_val[train_idx], y_train_val[val_idx]

                    model = build_mlp_model(input_dim, hidden_units, dropout_rate, learning_rate)

                    from tensorflow.keras.callbacks import EarlyStopping
                    early_stopping = EarlyStopping(
                        monitor='val_loss', patience=10, restore_best_weights=True, verbose=0
                    )

                    model.fit(
                        X_train_fold, y_train_fold,
                        validation_data=(X_val_fold, y_val_fold),
                        epochs=100, batch_size=32,
                        callbacks=[early_stopping], verbose=0
                    )

                    y_pred = model.predict(X_val_fold, verbose=0).flatten()
                    fold_scores['RMSE'].append(np.sqrt(mean_squared_error(y_val_fold, y_pred)))
                    fold_scores['MAE'].append(mean_absolute_error(y_val_fold, y_pred))
                    fold_scores['R2'].append(r2_score(y_val_fold, y_pred))

                results.append({
                    'hidden_units': hidden_units,
                    'dropout_rate': dropout_rate,
                    'learning_rate': learning_rate,
                    'RMSE': np.mean(fold_scores['RMSE']),
                    'RMSE_std': np.std(fold_scores['RMSE']),
                    'MAE': np.mean(fold_scores['MAE']),
                    'MAE_std': np.std(fold_scores['MAE']),
                    'R2': np.mean(fold_scores['R2']),
                    'R2_std': np.std(fold_scores['R2'])
                })
                print(f'参数组合: hidden_units={hidden_units}, dropout={dropout_rate}, lr={learning_rate} -> RMSE={results[-1]["RMSE"]:.4f}')

    results_df = pd.DataFrame(results)
    results_df.to_csv(OUTPUT_DIR / '网格搜索结果_完整.csv', index=False, encoding='utf-8-sig')
    print(f'\n网格搜索结果已保存: {OUTPUT_DIR / "网格搜索结果_完整.csv"}')

    # 找到各指标最优的参数组合
    best_rmse_idx = results_df['RMSE'].idxmin()
    best_mae_idx = results_df['MAE'].idxmin()
    best_r2_idx = results_df['R2'].idxmax()

    print(f'\n=== 最优参数汇总 ===')
    print(f'RMSE最优: RMSE={results_df.loc[best_rmse_idx, "RMSE"]:.4f}')
    print(f'  参数: hidden_units={results_df.loc[best_rmse_idx, "hidden_units"]}, '
          f'dropout_rate={results_df.loc[best_rmse_idx, "dropout_rate"]}, '
          f'learning_rate={results_df.loc[best_rmse_idx, "learning_rate"]}')
    print(f'MAE最优: MAE={results_df.loc[best_mae_idx, "MAE"]:.4f}')
    print(f'  参数: hidden_units={results_df.loc[best_mae_idx, "hidden_units"]}, '
          f'dropout_rate={results_df.loc[best_mae_idx, "dropout_rate"]}, '
          f'learning_rate={results_df.loc[best_mae_idx, "learning_rate"]}')
    print(f'R2最优: R2={results_df.loc[best_r2_idx, "R2"]:.4f}')
    print(f'  参数: hidden_units={results_df.loc[best_r2_idx, "hidden_units"]}, '
          f'dropout_rate={results_df.loc[best_r2_idx, "dropout_rate"]}, '
          f'learning_rate={results_df.loc[best_r2_idx, "learning_rate"]}')

    # 绘制参数寻优曲线
    plot_tuning_curves(results_df)

    # 返回以RMSE为准的最优参数
    best_params = {
        'hidden_units': int(results_df.loc[best_rmse_idx, 'hidden_units']),
        'dropout_rate': results_df.loc[best_rmse_idx, 'dropout_rate'],
        'learning_rate': results_df.loc[best_rmse_idx, 'learning_rate']
    }
    return best_params, results_df.loc[best_rmse_idx, 'RMSE']


def plot_tuning_curves(results):
    """绘制超参数寻优曲线，将所有图整合到一起"""
    params = ['hidden_units', 'dropout_rate', 'learning_rate']

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

    # ========== 图1: 3x3 子图网格 ==========
    fig, axes = plt.subplots(nrows=3, ncols=3, figsize=(20, 15))
    fig.suptitle('MLP超参数寻优曲线（5折交叉验证）', fontsize=18, y=0.98)

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

    # ========== 图2: 每个参数的三个指标对比图 ==========
    fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(24, 6))
    fig.suptitle('MLP超参数寻优指标对比（5折交叉验证）', fontsize=18, y=0.98)

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


def train_model(X_train, y_train, X_val, y_val, best_params=None):
    from tensorflow.keras.callbacks import EarlyStopping

    input_dim = X_train.shape[1]

    if best_params:
        model = build_mlp_model(input_dim,
                                hidden_units=best_params['hidden_units'],
                                dropout_rate=best_params['dropout_rate'],
                                learning_rate=best_params['learning_rate'])
    else:
        model = build_mlp_model(input_dim, hidden_units=128, dropout_rate=0.3, learning_rate=0.001)

    early_stopping = EarlyStopping(
        monitor='val_loss', patience=15, restore_best_weights=True, verbose=0
    )

    model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=200, batch_size=32,
        callbacks=[early_stopping], verbose=0
    )

    print(f'\n模型参数: hidden_units={best_params["hidden_units"] if best_params else 128}, '
          f'dropout_rate={best_params["dropout_rate"] if best_params else 0.3}, '
          f'learning_rate={best_params["learning_rate"] if best_params else 0.001}')
    return model


def evaluate_model(model, X, y_true):
    y_pred = model.predict(X, verbose=0).flatten()
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


def plot_results(y_true, y_pred, dates, residuals):
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(dates, y_true, label='实际AQI', color='#3b82f6', alpha=0.8, linewidth=1)
    ax.plot(dates, y_pred, label='预测AQI', color='#ef4444', alpha=0.8, linewidth=1)
    ax.set_xlabel('日期', fontsize=12)
    ax.set_ylabel('AQI', fontsize=12)
    ax.set_title('MLP: 实际AQI vs 预测AQI', fontsize=14)
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
    ax.set_title('MLP: 残差分析', fontsize=14)
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
    ax.set_title('MLP: 实际值 vs 预测值散点图', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / '拟合散点图.png', dpi=300, bbox_inches='tight')
    plt.close()


def main():
    print('=' * 60)
    print('MLP预测模型')
    print('=' * 60)

    train, val, test = load_data()

    X_train = train[FEATURE_COLS].values
    y_train = train[TARGET_COL].values
    X_val = val[FEATURE_COLS].values
    y_val = val[TARGET_COL].values
    X_test = test[FEATURE_COLS].values
    y_test = test[TARGET_COL].values
    dates = test['日期'].dt.strftime('%Y-%m-%d').values

    # 数据标准化
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)

    # 合并训练集和验证集用于网格搜索
    X_train_val = np.vstack([X_train_scaled, X_val_scaled])
    y_train_val = np.concatenate([y_train, y_val])

    # 超参数寻优
    best_params, cv_rmse = grid_search_tuning(X_train_val, y_train_val)

    # 使用最优参数训练模型
    print('\n使用最优参数训练模型...')
    model = train_model(X_train_scaled, y_train, X_val_scaled, y_val, best_params)

    print('\n验证集评估...')
    _, val_rmse, val_mae, val_r2 = evaluate_model(model, X_val_scaled, y_val)
    print(f'  RMSE: {val_rmse:.4f}, MAE: {val_mae:.4f}, R2: {val_r2:.4f}')

    print('\n测试集评估...')
    y_pred, test_rmse, test_mae, test_r2 = evaluate_model(model, X_test_scaled, y_test)
    print(f'  RMSE: {test_rmse:.4f}, MAE: {test_mae:.4f}, R2: {test_r2:.4f}')

    metrics = {
        '模型': 'MLP',
        'CV_RMSE': round(cv_rmse, 4),
        'RMSE': round(test_rmse, 4),
        'MAE': round(test_mae, 4),
        'R2': round(test_r2, 4)
    }

    residuals = y_test - y_pred
    save_results(y_test, y_pred, dates, metrics, best_params)
    plot_results(y_test, y_pred, pd.to_datetime(dates), residuals)

    print('\nMLP预测完成！')


if __name__ == '__main__':
    main()
