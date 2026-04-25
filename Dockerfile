FROM python:3.11-slim

WORKDIR /app

# 先复制依赖文件，利用 Docker 层缓存
COPY pyproject.toml .

# 安装依赖（需要先复制 src 目录才能 pip install -e）
COPY src/ src/
RUN pip install --no-cache-dir -e .

# 复制其余文件
COPY main.py .

EXPOSE 8000
CMD ["python", "main.py"]
