FROM python:3.11-slim

WORKDIR /app

# 先复制依赖描述文件，利用 Docker 层缓存加速重复构建
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

COPY . .

EXPOSE 8000
CMD ["python", "main.py"]
