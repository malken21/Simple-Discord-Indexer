# ビルドステージ
# アプリケーションの依存関係をビルドするために、完全な Python 環境を使用
FROM python:3.11-slim-bookworm AS builder

# 作業ディレクトリを設定
WORKDIR /app

# ビルドに必要なツール (コンパイラなど) をインストール
# discord.py (aiohttp) などの依存関係のビルドに必要
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt をコピーして依存関係をインストール
COPY requirements.txt .

# システムディレクトリではなく、特定のディレクトリに依存関係をインストール
# これにより、ランタイムステージへのコピーが容易になります
RUN pip install --no-cache-dir --target=/app/site-packages -r requirements.txt

# データディレクトリを作成し、非 root ユーザーの権限を設定
# (distroless はシェルを持たないため、この段階で権限設定を行う必要があります)
RUN mkdir /app/data && chown 65532:65532 /app/data

# ランタイムステージ
# Google の distroless イメージを使用 (軽量、セキュア)
# https://github.com/GoogleContainerTools/distroless
# タグに nonroot を含めることで、非 root ユーザーが含まれていることを明示する場合もありますが、
# python3-debian12 にはデフォルトで nonroot ユーザーが含まれています。
FROM gcr.io/distroless/python3-debian12

# Python がモジュールを検索するパスを追加
ENV PYTHONPATH=/app/site-packages
# Python のバッファリングを無効化 (ログを即座に出力するため)
ENV PYTHONUNBUFFERED=1
# .pyc ファイルの生成を抑制
ENV PYTHONDONTWRITEBYTECODE=1

# 作業ディレクトリを設定
WORKDIR /app

# ビルドステージからインストール済みの依存関係をコピー
COPY --from=builder --chown=nonroot:nonroot /app/site-packages /app/site-packages

# ビルドステージからデータディレクトリをコピー
COPY --from=builder --chown=nonroot:nonroot /app/data /app/data

# アプリケーションコードをコピー
COPY --chown=nonroot:nonroot . .

# セキュリティのため、非 root ユーザー (ID 65532) で実行
USER nonroot

# 永続データ用のボリューム
VOLUME ["/app/data"]

# アプリケーションを実行
CMD ["main.py"]
