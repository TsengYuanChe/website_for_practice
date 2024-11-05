FROM python:3.12.6

# 更新 apt 環境並安裝必要的工具
RUN apt-get update && \
    apt-get install -y sqlite3 libsqlite3-dev libgl1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/

# 複製並安裝需求的 Python 套件
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --timeout=1000 torch==2.5.0 torchvision==0.20.0 && \
    pip install --timeout=1000 -r requirements.txt

# 複製應用程式源碼
COPY . .

# 設定 Flask 環境變數
ENV FLASK_APP=app:create_app
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0
ENV PYTHONPATH=/usr/src
ENV IMAGE_URL=/storage/images/
ENV FLASK_RUN_PORT=8080
ENV FLASK_RUN_HOST=0.0.0.0

# 暴露 8080 埠給 Cloud Run
EXPOSE 8080

# 使用 init_db.py 初始化資料庫，並啟動 gunicorn
CMD ["sh", "-c", "python init_db.py && gunicorn -w 4 -b :8080 'app:create_app()'"]