# Simple-Discord-Indexer

Discord サーバーのメッセージログ、フォーラムスレッド、添付ファイルを自動収集し、**検索可能なナレッジベース**として構築するためのツールです。

---

## 概要

このツールは、指定された Discord サーバー（ギルド）内の全チャンネル・フォーラムからデータを取得し、ローカル環境にバックアップします。
取得したデータは、人間が読みやすい **Markdown** 形式と、プログラム処理に適した **JSONL** 形式の両方で保存されます。
ナレッジの蓄積、サーバー移行時のバックアップ、あるいはオフラインでの閲覧に最適です。

### 主な機能

- **完全な階層構造**: カテゴリ、チャンネル、フォーラムスレッドの構造をそのままディレクトリとして再現。
- **マルチフォーマット**:
  - **Markdown**: 閲覧性に優れ、Obsidian 等のナレッジベースツールと互換性があります。
  - **JSONL**: データ分析や機械学習のデータセットとして利用しやすい形式です。
- **添付ファイル保存**: 画像やドキュメントなどの添付ファイルも自動ダウンロードし、リンクを保持します。
- **差分更新**: 初回は全取得、2回目以降は新着メッセージのみを効率的に取得します。
- **柔軟な設定**: 特定カテゴリの除外や、対象チャンネルの指定が可能です。

---

## 保存データの構造

データは `data/` ディレクトリ配下に以下の構造で保存されます。

```text
data/                               # 取得データの保存先
├── fetch_state.json                # 取得状況の管理ファイル
└── (Guild Name)/                   # サーバーごとのデータ
    └── (Category)/                 # カテゴリフォルダ
        └── (Channel)/              # チャンネルフォルダ
            ├── messages.md         # 閲覧用ログ
            ├── messages.jsonl      # データ用ログ
            └── attachments/        # 添付ファイル
```

---

## セットアップ

### 1. 前提条件

- **Python 3.8 以上**
- **Discord Bot Token**
  - Developer Portal で Bot を作成し、以下の **Privileged Gateway Intents** を有効にしてください。
    - `MESSAGE CONTENT INTENT` (メッセージ内容の読み取りに必須)
    - `SERVER MEMBERS INTENT` (メンバー情報の取得に必要)

### 2. インストール

リポジトリをクローンし、依存パッケージをインストールします。

```bash
git clone https://github.com/malken21/Simple-Discord-Indexer
cd Simple-Discord-Indexer
pip install -r requirements.txt
```

### 3. 設定ファイル（.env / config.yaml）の準備

プロジェクトルートに以下の2つのファイルを用意してください。

#### .env (推奨)

Bot Token を設定します。`.env.example` をコピーして作成してください。

```env
DISCORD_TOKEN=your_discord_bot_token_here
```

#### config.yaml (必須)

取得対象のサーバーIDやカテゴリなどの詳細設定を行います。`config.yaml.example` をコピーして作成し、必要事項を記入してください。

```yaml
discord:
  guild_id: 123456789012345678  # 対象サーバーID
indexing:
  allowed_categories:            # 取得対象カテゴリ（リスト形式）
    - "general"
```

---

## 使い方

以下のコマンドを実行すると、同期が開始されます。

```bash
python main.py
```

実行中はログが表示され、取得の進捗が確認できます。
完了すると設定した保存先ディレクトリにサーバー名のフォルダが作成され、そこに全てのログが保存されます。

---

## Docker での実行

GitHub Container Registry (GHCR) で公開されている公式イメージを使用して簡単に実行できます。

### 1. イメージの取得

```bash
docker pull ghcr.io/malken21/simple-discord-indexer:latest
```

### 2. 設定ファイルの準備

カレントディレクトリに `.env` と `config.yaml` を用意してください。

### 3. Docker Compose での実行

プロジェクトルートに `docker-compose.yaml` を作成し、以下の内容を記述します。

```yaml
services:
  discord-indexer:
    image: ghcr.io/malken21/simple-discord-indexer:latest
    volumes:
      - ./data:/app/data
      - ./config.yaml:/app/config.yaml
      - ./.env:/app/.env
```

起動とログの確認：

```bash
docker compose up -d
docker compose logs -f
```

### 4. docker run での直接実行

Docker Compose を使用せずに直接実行する場合：

```bash
docker run -d \
  --name discord-indexer \
  -v ./data:/app/data \
  -v ./config.yaml:/app/config.yaml \
  -v ./.env:/app/.env \
  ghcr.io/malken21/simple-discord-indexer:latest
```
