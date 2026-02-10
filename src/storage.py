import os
import json
import logging
from typing import Dict, List, Any, Optional
import discord
from .config import STATE_FILE, LOGGER_NAME
from .formatter import MessageFormatter

logger = logging.getLogger(LOGGER_NAME)

class StorageManager:
    """
    メッセージの保存と状態管理を行うクラス。
    データのバッファリングとフラッシュを管理します。
    """
    def __init__(self, batch_size: int = 100):
        self.fetch_state: Dict[str, Any] = self.load_state()
        self.batch_size: int = batch_size
        self.buffer_content_md: Dict[str, str] = {}
        self.buffer_content_jsonl: List[str] = []
        self.current_batch_count: int = 0

    def load_state(self) -> Dict[str, Any]:
        """保存された状態を読み込みます。"""
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error(f"状態ファイル {STATE_FILE} の読み込みに失敗しました。")
                return {}
        return {}

    def save_state(self) -> None:
        """現在の状態をファイルに保存します。"""
        try:
            with open(STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.fetch_state, f, indent=4)
        except Exception as e:
            logger.error(f"状態ファイルの保存に失敗しました: {e}")

    def get_last_message_id(self, key: str) -> Optional[int]:
        """指定されたキー（チャンネルIDなど）の最後のメッセージIDを取得します。"""
        return self.fetch_state.get(key)

    def update_last_message_id(self, key: str, message_id: int) -> None:
        """指定されたキーの最後のメッセージIDを更新します。"""
        self.fetch_state[key] = message_id

    async def add_message(self, message: discord.Message, attachments_dir: str, messages_dir: str, jsonl_file: str) -> None:
        """
        メッセージをバッファに追加します。
        バッファサイズが閾値に達した場合、自動的にフラッシュします。
        """
        # --- Markdownフォーマット & 添付ファイル保存 ---
        # 保存されたファイル名を取得するために先に実行する
        attachment_rel_paths = []
        try:
            formatted_msg, attachment_filenames = await MessageFormatter.to_markdown(message, attachments_dir)
            
            # JSONL用の相対パスを作成
            attachment_rel_paths = [f"attachments/{fname}" for fname in attachment_filenames]

            msg_date_str = message.created_at.strftime('%Y-%m-%d')
            
            if msg_date_str not in self.buffer_content_md:
                self.buffer_content_md[msg_date_str] = ""
            
            self.buffer_content_md[msg_date_str] += formatted_msg
        except Exception as e:
            logger.error(f"メッセージID {message.id} のMarkdown変換中にエラーが発生しました: {e}")

        # --- JSONLデータの準備 ---
        try:
            msg_data = {
                "id": message.id,
                "author": {
                    "id": message.author.id,
                    "name": message.author.name,
                    "discriminator": message.author.discriminator,
                    "display_name": message.author.display_name,
                    "bot": message.author.bot
                },
                "content": message.content,
                "clean_content": message.clean_content,
                "created_at": str(message.created_at),
                "edited_at": str(message.edited_at) if message.edited_at else None,
                "attachments": attachment_rel_paths, # ローカルパスを使用
                "embeds": [e.to_dict() for e in message.embeds],
                "reference": {
                    "message_id": message.reference.message_id,
                    "channel_id": message.reference.channel_id,
                    "guild_id": message.reference.guild_id
                } if message.reference else None,
                "reactions": [{
                    "emoji": str(r.emoji),
                    "count": r.count
                } for r in message.reactions]
            }
            self.buffer_content_jsonl.append(json.dumps(msg_data, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"メッセージID {message.id} のJSONデータ作成中にエラーが発生しました: {e}")

        self.current_batch_count += 1

        # バッファが一杯になったら書き込む
        if self.current_batch_count >= self.batch_size:
            self.flush(messages_dir, jsonl_file)

    def flush(self, messages_dir: str, jsonl_file: str) -> None:
        """バッファ内のデータをファイルに書き込み、バッファをクリアします。"""
        if not self.buffer_content_md and not self.buffer_content_jsonl:
            return

        # Markdownファイルの書き込み
        for date_str, content in self.buffer_content_md.items():
            md_file_path = os.path.join(messages_dir, f"{date_str}.md")
            try:
                # 新規の場合はファイルを初期化（ヘッダー書き込み）
                if not os.path.exists(md_file_path):
                    with open(md_file_path, 'w', encoding='utf-8') as f:
                        f.write(f"# {date_str}\n\n")
                
                with open(md_file_path, 'a', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                logger.error(f"Markdownファイル {md_file_path} への書き込みに失敗しました: {e}")
        
        # JSONLの書き込み
        if self.buffer_content_jsonl:
            try:
                with open(jsonl_file, 'a', encoding='utf-8') as f:
                    for line in self.buffer_content_jsonl:
                        f.write(line)
            except Exception as e:
                logger.error(f"JSONLファイル {jsonl_file} への書き込みに失敗しました: {e}")

        # バッファのリセット
        self.buffer_content_md.clear()
        self.buffer_content_jsonl.clear()
        self.current_batch_count = 0

