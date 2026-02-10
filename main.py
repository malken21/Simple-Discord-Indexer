import logging
from src.fetch_logs import run_fetcher
from src.config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

def main():
    """
    プログラムのエントリーポイント
    """
    try:
        logger.info("Simple-Discord-Indexer を開始します。")
        run_fetcher()
    except KeyboardInterrupt:
        logger.info("ユーザーによって中断されました。")
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {e}", exc_info=True)

if __name__ == "__main__":
    main()
