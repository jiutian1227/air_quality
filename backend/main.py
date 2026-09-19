from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Text, func
from sqlalchemy.orm import sessionmaker, Session, declarative_base
import uvicorn
from datetime import date
import os
from pathlib import Path
import numpy as np
import pandas as pd


import joblib
import json
# 模型路径配置
BASE_DIR = Path(__file__).parent.parent
CLUSTER_MODEL_DIR = BASE_DIR / 'result' / '降维聚类' / 'model'
LINEAR_MODEL_DIR = BASE_DIR / 'result' / '预测分析' / '线性回归' / 'model'
LIGHTGBM_MODEL_DIR = BASE_DIR / 'result' / '预测分析' / 'LightGBM' / 'model'

# 全局模型变量
cluster_scaler = None
cluster_pca = None
cluster_kmeans = None
cluster_meta = None
linear_model = None
linear_meta = None
lightgbm_model = None
lightgbm_meta = None
pca_cluster_scatter = None


def load_models():
    """启动时加载训练好的模型"""
    global cluster_scaler, cluster_pca, cluster_kmeans, cluster_meta
    global linear_model, linear_meta, lightgbm_model, lightgbm_meta, pca_cluster_scatter

    try:
        if CLUSTER_MODEL_DIR.exists():
            cluster_scaler = joblib.load(CLUSTER_MODEL_DIR / 'scaler.pkl')
            cluster_pca = joblib.load(CLUSTER_MODEL_DIR / 'pca.pkl')
            cluster_kmeans = joblib.load(CLUSTER_MODEL_DIR / 'kmeans.pkl')
            with open(CLUSTER_MODEL_DIR / 'cluster_meta.json', 'r', encoding='utf-8') as f:
                cluster_meta = json.load(f)
            print('聚类模型加载成功')
    except Exception as e:
        print(f'聚类模型加载失败: {e}')

    try:
        if LINEAR_MODEL_DIR.exists():
            linear_model = joblib.load(LINEAR_MODEL_DIR / 'linear_regression.pkl')
            with open(LINEAR_MODEL_DIR / 'linear_regression_meta.json', 'r', encoding='utf-8') as f:
                linear_meta = json.load(f)
            print('线性回归模型加载成功')
    except Exception as e:
        print(f'线性回归模型加载失败: {e}')

    try:
        if LIGHTGBM_MODEL_DIR.exists():
            lightgbm_model = joblib.load(LIGHTGBM_MODEL_DIR / 'lightgbm.pkl')
            with open(LIGHTGBM_MODEL_DIR / 'lightgbm_meta.json', 'r', encoding='utf-8') as f:
                lightgbm_meta = json.load(f)
            print('LightGBM模型加载成功')
    except Exception as e:
        print(f'LightGBM模型加载失败: {e}')

    # 加载PCA聚类散点数据（用于前端聚类散点图）
    try:
        pca_csv_path = BASE_DIR / 'result' / '降维聚类' / '数据' / 'PCA聚类结果.csv'
        if pca_csv_path.exists():
            df = pd.read_csv(pca_csv_path)
            pca_cluster_scatter = df[['PC1', 'PC2', '聚类']].to_dict(orient='records')
            print(f'PCA聚类散点数据加载成功，共{len(pca_cluster_scatter)}条记录')
    except Exception as e:
        print(f'PCA聚类散点数据加载失败: {e}')


# 数据库配置
DATABASE_URL = "mysql+pymysql://root:123456789zyx@localhost:3306/air_quality_platform"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 用户模型
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(Integer, default=2)

# FastAPI应用
app = FastAPI(title="空气质量平台API")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic模型
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: int = 2

class UserResponse(BaseModel):
    id: int
    username: str
    role: int

class UserUpdateRequest(BaseModel):
    username: str = None
    password: str = None
    role: int = None

# 数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 获取当前用户（从请求头获取用户信息）
def get_current_user(
    username: str = Header(None),
    db: Session = Depends(get_db)
):
    if username:
        user = db.query(User).filter(User.username == username).first()
        if user:
            return {"id": user.id, "username": user.username, "role": user.role}
    return {"role": 2}

# 登录接口
@app.post("/api/login", response_model=UserResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == request.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    if user.password != request.password:
        raise HTTPException(status_code=401, detail="密码错误")
    return UserResponse(id=user.id, username=user.username, role=user.role)

# 注册接口
@app.post("/api/register", response_model=UserResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    # 检查用户是否存在
    existing_user = db.query(User).filter(User.username == request.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="用户已存在")
    
    # 创建新用户
    new_user = User(
        username=request.username,
        password=request.password,
        role=request.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return UserResponse(id=new_user.id, username=new_user.username, role=new_user.role)

# 获取用户信息
@app.get("/api/user/{username}", response_model=UserResponse)
def get_user(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return UserResponse(id=user.id, username=user.username, role=user.role)


# ==================== 机器学习预测接口 ====================

# 聚类预测请求体
class ClusterPredictRequest(BaseModel):
    pm25: float
    pm10: float
    no2: float
    so2: float
    co: float
    o3: float
    aqi_lag1: float
    pm25_roll7_mean: float


# 线性回归预测请求体
class LinearPredictRequest(BaseModel):
    pm25: float
    pm10: float
    no2: float
    so2: float
    co: float
    o3: float
    aqi_lag1: float
    pm25_roll7_mean: float


@app.post("/api/predict/cluster")
def predict_cluster(request: ClusterPredictRequest):
    """聚类预测：输入8个特征，输出所属聚类类别与名称"""
    if cluster_scaler is None or cluster_pca is None or cluster_kmeans is None:
        raise HTTPException(status_code=503, detail="聚类模型未加载，请先运行训练脚本")

    # 按 meta 中的特征顺序构造输入
    features_order = cluster_meta['features']
    values_map = {
        'PM2.5': request.pm25,
        'PM10': request.pm10,
        'NO2': request.no2,
        'SO2': request.so2,
        'CO': request.co,
        'O3': request.o3,
        'AQI_lag1': request.aqi_lag1,
        'PM2.5_roll7_mean': request.pm25_roll7_mean,
    }
    x = np.array([[values_map[f] for f in features_order]])

    x_scaled = cluster_scaler.transform(x)
    x_pca = cluster_pca.transform(x_scaled)
    cluster_id = int(cluster_kmeans.predict(x_pca)[0])
    cluster_name = cluster_meta['cluster_names'][cluster_id] if cluster_id < len(cluster_meta['cluster_names']) else f'聚类{cluster_id+1}'

    # 计算到各聚类中心的距离
    distances = cluster_kmeans.transform(x_pca)[0].tolist()
    distances_map = {f'聚类{i+1}': round(float(d), 4) for i, d in enumerate(distances)}

    # 获取各聚类质心的PCA坐标（用于前端散点图）
    centroids = []
    for i, centroid in enumerate(cluster_kmeans.cluster_centers_):
        # 质心已经在PCA空间中，不需要再transform
        centroids.append({
            'cluster_id': i,
            'cluster_name': cluster_meta['cluster_names'][i] if i < len(cluster_meta['cluster_names']) else f'聚类{i+1}',
            'pc1': float(centroid[0]),
            'pc2': float(centroid[1])
        })

    return {
        'cluster_id': cluster_id,
        'cluster_name': cluster_name,
        'distances': distances_map,
        'pc1': float(x_pca[0, 0]),
        'pc2': float(x_pca[0, 1]),
        'centroids': centroids
    }


@app.post("/api/predict/linear")
def predict_linear(request: LinearPredictRequest):
    """线性回归预测：输入8个特征，输出预测的AQI"""
    if linear_model is None:
        raise HTTPException(status_code=503, detail="线性回归模型未加载，请先运行训练脚本")

    features_order = linear_meta['features']
    values_map = {
        'PM2.5': request.pm25,
        'PM10': request.pm10,
        'NO2': request.no2,
        'SO2': request.so2,
        'CO': request.co,
        'O3': request.o3,
        'AQI_lag1': request.aqi_lag1,
        'PM2.5_roll7_mean': request.pm25_roll7_mean,
    }
    x = np.array([[values_map[f] for f in features_order]])
    y_pred = float(linear_model.predict(x)[0])

    # AQI等级
    if y_pred <= 50:
        level = '优'
    elif y_pred <= 100:
        level = '良'
    elif y_pred <= 150:
        level = '轻度污染'
    elif y_pred <= 200:
        level = '中度污染'
    elif y_pred <= 300:
        level = '重度污染'
    else:
        level = '严重污染'

    return {
        'predicted_aqi': round(y_pred, 2),
        'level': level
    }


@app.post("/api/predict/lightgbm")
def predict_lightgbm(request: LinearPredictRequest):
    """LightGBM预测：输入8个特征，输出预测的AQI"""
    if lightgbm_model is None:
        raise HTTPException(status_code=503, detail="LightGBM模型未加载，请先运行训练脚本")

    features_order = lightgbm_meta['features']
    values_map = {
        'PM2.5': request.pm25,
        'PM10': request.pm10,
        'NO2': request.no2,
        'SO2': request.so2,
        'CO': request.co,
        'O3': request.o3,
        'AQI_lag1': request.aqi_lag1,
        'PM2.5_roll7_mean': request.pm25_roll7_mean,
    }
    x = np.array([[values_map[f] for f in features_order]])
    y_pred = float(lightgbm_model.predict(x)[0])

    # AQI等级
    if y_pred <= 50:
        level = '优'
    elif y_pred <= 100:
        level = '良'
    elif y_pred <= 150:
        level = '轻度污染'
    elif y_pred <= 200:
        level = '中度污染'
    elif y_pred <= 300:
        level = '重度污染'
    else:
        level = '严重污染'

    return {
        'predicted_aqi': round(y_pred, 2),
        'level': level
    }


@app.get("/api/predict/cluster-scatter")
def get_cluster_scatter_data():
    """返回PCA聚类散点数据（所有历史点的PC1/PC2坐标和聚类标签）"""
    if pca_cluster_scatter is None:
        raise HTTPException(status_code=503, detail="PCA聚类散点数据未加载")
    return pca_cluster_scatter


@app.get("/api/predict/info")
def predict_info():
    """获取模型基本信息（特征顺序、聚类命名等）"""
    return {
        'cluster_loaded': cluster_kmeans is not None,
        'linear_loaded': linear_model is not None,
        'lightgbm_loaded': lightgbm_model is not None,
        'cluster_features': cluster_meta['features'] if cluster_meta else None,
        'cluster_names': cluster_meta['cluster_names'] if cluster_meta else None,
        'linear_features': linear_meta['features'] if linear_meta else None,
        'lightgbm_features': lightgbm_meta['features'] if lightgbm_meta else None,
    }


if __name__ == "__main__":
    load_models()
    uvicorn.run(app, host="0.0.0.0", port=8000)