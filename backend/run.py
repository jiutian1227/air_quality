import csv
import pymysql

# 数据库配置
host = "localhost"
port = 3306
user = "root"
password = "123456789zyx"
db_name = "air_quality_platform"
table = "data_lanzhou"
# 正确完整路径
csv_path = r"F:\PythonProject\课程设计\visualization_course\data\兰州市_cleaned.csv"

# 连接数据库
conn = pymysql.connect(
    host=host,
    port=port,
    user=user,
    password=password,
    database=db_name,
    charset="utf8mb4"
)
cur = conn.cursor()

# 清空数据表
cur.execute(f"TRUNCATE TABLE {table};")
conn.commit()
print("✅ 已清空数据表")

# 插入语句
insert_sql = """
INSERT INTO data_lanzhou (date,aqi,quality_grade,aqi_rank,pm25,pm10,no2,so2,co,o3)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
"""

# 判断分隔符（修正变量csv_path）
with open(csv_path, "r", encoding="gbk") as f:
    first_line = f.readline()
delimiter = "\t" if "\t" in first_line else ","

# 逐行读取写入
with open(csv_path, "r", encoding="gbk") as f:
    reader = csv.reader(f, delimiter=delimiter)
    next(reader)  # 跳过表头
    count = 0
    for row in reader:
        # 过滤残缺行
        if len(row) != 11:
            continue
        city, date, aqi, grade, rank, pm25, pm10, no2, so2, co, o3 = row
        # 转换日期格式
        y, m, d = date.split("/")
        new_date = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
        params = (new_date, aqi, grade, rank, pm25, pm10, no2, so2, co, o3)
        cur.execute(insert_sql, params)
        count += 1
        # 每100条提交一次
        if count % 100 == 0:
            conn.commit()
            print(f"已导入 {count} 条")

# 提交剩余数据
conn.commit()
print(f"导入完成，总记录：{count} 条")

# 关闭连接
cur.close()
conn.close()