import os
import logging
import yaml
from typing import List, Optional
from dotenv import load_dotenv

# 環境変数を読み込む
load_dotenv()

# パス
BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH: str = os.path.join(BASE_DIR, 'config.yaml')

# デフォルト設定
default_config = {
    'discord': {
        'token': None,
        'guild_id': 0
    },
    'indexing': {
        'allowed_categories': []
    },
    'logging': {
        'name': "Simple-Discord-Indexer",
        'level': "INFO"
    },
    'paths': {
        'data_dir': 'data'
    }
}

# YAMLから設定を読み込む
config = default_config
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        loaded_config = yaml.safe_load(f)
        if loaded_config:
            # 辞書を再帰的に更新する（簡易版）
            for key, value in loaded_config.items():
                if isinstance(value, dict) and key in config:
                    config[key].update(value)
                else:
                    config[key] = value

# 個別の設定値に展開
LOGGER_NAME: str = config['logging']['name']
LOG_LEVEL: str = config['logging']['level']

# ロギング設定
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(LOGGER_NAME)

DISCORD_TOKEN: Optional[str] = os.getenv('DISCORD_TOKEN') or config['discord'].get('token')
GUILD_ID: int = int(config['discord'].get('guild_id', 0))
ALLOWED_CATEGORIES: List[str] = config['indexing'].get('allowed_categories', [])

# 必須環境変数の検証
if not DISCORD_TOKEN:
    logger.critical("DISCORD_TOKEN が設定されていません。.env または config.yaml を確認してください。")

DATA_DIR: str = os.path.join(BASE_DIR, config['paths'].get('data_dir', '../Cafe-Horizon-Discord-Vault'))
KNOWLEDGE_BASE_DIR: str = DATA_DIR
STATE_FILE: str = os.path.join(DATA_DIR, 'fetch_state.json')

# ディレクトリが存在することを確認
os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)

