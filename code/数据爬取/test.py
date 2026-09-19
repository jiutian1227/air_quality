import os
import csv
import random
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import lxml


# 创建存储目录
SAVE_DIR = Path(__file__).parent.parent.parent / 'data'
SAVE_DIR.mkdir(parents=True, exist_ok=True)

# 兰州市配置
CITY_CONFIG = {
    "lanzhou": "兰州市"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}

def crawl_single_city(pinyin, city_name):
    file_path = SAVE_DIR / f"{city_name}_2014-2026空气质量.csv"
    # 单个城市独立文件，爬完就关闭
    with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["城市", "日期", "AQI", "质量等级", "AQI排名", "PM2.5", "PM10", "NO2", "SO2", "CO", "O3"]
        )
        writer.writeheader()
        now_year = datetime.now().year

        for year in range(2014, 2027):
            for month in range(1, 13):
                if year == now_year and month > datetime.now().month:
                    continue
                print(f"{city_name}:{year}年{month:02d}月")
                url = f"https://www.tianqihoubao.com/aqi/{pinyin}-{year}{month:02d}.html"
                try:
                    resp = requests.get(url, headers=headers, timeout=60)
                    resp.raise_for_status()
                except Exception as e:
                    print("fa")
                    time.sleep(2)
                    continue
                time.sleep(random.uniform(1, 2.5))

                soup = BeautifulSoup(resp.text, "lxml")
                rows = soup.find_all("tr")
                for row in rows[1:]:
                    cols = row.find_all("td")
                    if len(cols) < 10:
                        continue
                    row_data = {
                        "城市": city_name,
                        "日期": cols[0].get_text(strip=True),
                        "AQI": cols[1].get_text(strip=True),
                        "质量等级": cols[2].get_text(strip=True),
                        "AQI排名": cols[3].get_text(strip=True),
                        "PM2.5": cols[4].get_text(strip=True),
                        "PM10": cols[5].get_text(strip=True),
                        "NO2": cols[6].get_text(strip=True),
                        "SO2": cols[7].get_text(strip=True),
                        "CO": cols[8].get_text(strip=True),
                        "O3": cols[9].get_text(strip=True)
                    }
                    writer.writerow(row_data)
    print(f"{city_name} 数据已完整保存至: {file_path}\n")

if __name__ == "__main__":
    for py, name in CITY_CONFIG.items():
        crawl_single_city(py, name)
    print("数据爬取完成！")
