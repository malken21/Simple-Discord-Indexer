# ビルドステージ
FROM python:3.11-slim-bookworm AS builder
WORKDIR /app

# 依存関係のビルドに必要なツールをインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --target=/app/site-packages -r requirements.txt
RUN mkdir /app/data

# ランタイムステージ
FROM gcr.io/distroless/python3-debian12
ENV PYTHONPATH=/app/site-packages \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY --from=builder /app/site-packages /app/site-packages
COPY --from=builder /app/data /app/data
COPY . .

# ボリューム権限の問題を回避するため、rootユーザーで実行
USER 0

VOLUME ["/app/data"]
CMD ["main.py"]
