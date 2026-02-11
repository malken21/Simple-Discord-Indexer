import discord
import os
import json
import datetime
import logging
from .config import DISCORD_TOKEN, GUILD_ID, KNOWLEDGE_BASE_DIR, ALLOWED_CATEGORIES, LOGGER_NAME
from .storage import StorageManager
from .utils import sanitize, replace_fake_uppercase

# ロガーの設定
logger = logging.getLogger(LOGGER_NAME)

class DiscordFetcher(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.storage = StorageManager()

    async def on_ready(self) -> None:
        logger.info(f'{self.user} としてログインしました (ID: {self.user.id})')
        try:
            await self.fetch_all_logs()
        except Exception as e:
            logger.error(f"実行中にエラーが発生しました: {e}", exc_info=True)
        finally:
            logger.info('プロセスを終了します。')
            await self.close()

    async def fetch_all_logs(self) -> None:
        guild = self.get_guild(GUILD_ID)
        if not guild:
            logger.error(f'ID {GUILD_ID} のギルドが見つかりません。')
            return

        logger.info(f'ギルドのログを取得中: {guild.name}')
        
        updated = False
        
        # テキストチャンネルとフォーラムを取得
        channels = [c for c in guild.channels if isinstance(c, (discord.TextChannel, discord.ForumChannel))]
        
        for channel in channels:
            category_name = replace_fake_uppercase(channel.category.name if channel.category else "Uncategorized")
            # カテゴリ名が許可リストにない、かつ（カテゴリなしの場合に空文字列が許可リストにない）場合はスキップ
            if category_name not in ALLOWED_CATEGORIES and not (not channel.category and "" in ALLOWED_CATEGORIES):
                continue
            logger.info(f'チャンネルを処理中: {channel.name} (ID: {channel.id}) カテゴリ: {category_name}')
            
            # 1. チャンネル自体の処理（テキストチャンネルの場合）
            if isinstance(channel, discord.TextChannel):
                if await self.process_messageable(channel, category_path=category_name, channel_name=replace_fake_uppercase(channel.name), file_name="messages"):
                    updated = True

            # 2. アクティブなスレッドの処理
            try:
                if hasattr(channel, 'threads'):
                    for thread in channel.threads:
                        logger.info(f'  スレッドを処理中: {thread.name}')
                        if await self.process_messageable(thread, category_path=category_name, channel_name=replace_fake_uppercase(channel.name), file_name=replace_fake_uppercase(thread.name), is_thread=True):
                            updated = True
            except Exception as e:
                logger.error(f"  {channel.name} のスレッドへのアクセスエラー: {e}")

            # 3. アーカイブされたスレッドの処理（フォーラムチャンネル固有）
            if isinstance(channel, discord.ForumChannel):
                logger.info(f"  フォーラムのアーカイブされたスレッドを取得中: {channel.name}")
                try:
                    async for thread in channel.archived_threads(limit=None):
                        logger.info(f'  アーカイブされたスレッドを処理中: {thread.name}')
                        if await self.process_messageable(thread, category_path=category_name, channel_name=replace_fake_uppercase(channel.name), file_name=replace_fake_uppercase(thread.name), is_thread=True):
                            updated = True
                except Exception as e:
                    logger.error(f"  {channel.name} のアーカイブされたスレッドへのアクセスエラー: {e}")

            # 4. アーカイブされたスレッドの処理（テキストチャンネルの場合）
            if isinstance(channel, discord.TextChannel):
                logger.info(f"  テキストチャンネルのアーカイブされたスレッドを取得中: {channel.name}")
                try:
                    async for thread in channel.archived_threads(limit=None):
                        logger.info(f'  アーカイブされたスレッドを処理中: {thread.name}')
                        if await self.process_messageable(thread, category_path=category_name, channel_name=replace_fake_uppercase(channel.name), file_name=replace_fake_uppercase(thread.name), is_thread=True):
                            updated = True
                except Exception as e:
                    logger.error(f"  {channel.name} のアーカイブされたスレッドへのアクセスエラー: {e}")

        # ギルドのアクティブなスレッドを処理（channel.threadsで見つからないスレッドのフォールバック）
        logger.info('アクティブなスレッドを処理中 (ギルド全体チェック)...')
        for thread in guild.threads:
            if thread.parent_id and thread.guild.id == GUILD_ID:
                 parent = guild.get_channel(thread.parent_id)
                 if parent and isinstance(parent, (discord.TextChannel, discord.ForumChannel)):
                    parent_category = replace_fake_uppercase(parent.category.name if parent.category else "Uncategorized")
                    # 親カテゴリ名が許可リストにない、かつ（親カテゴリなしの場合に空文字列が許可リストにない）場合はスキップ
                    if parent_category not in ALLOWED_CATEGORIES and not (not parent.category and "" in ALLOWED_CATEGORIES):
                        continue
                    logger.info(f'  スレッドを処理中: {thread.name} (親: {parent.name} カテゴリ: {parent_category})')
                    if await self.process_messageable(thread, category_path=parent_category, channel_name=replace_fake_uppercase(parent.name), file_name=replace_fake_uppercase(thread.name), is_thread=True):
                        updated = True

        self.storage.save_state()
        
        if updated:
            logger.info('ログが更新されました。')
        
        logger.info('完了。')

    async def process_messageable(self, messageable: discord.abc.Messageable, category_path: str, channel_name: str, file_name: str="MainChat", is_thread: bool=False) -> bool:
        """
        メッセージを取得し、保存処理をStorageManagerに委譲します。
        """
        # 状態追跡用の一意ID
        state_key = str(messageable.id)
        last_message_id = self.storage.get_last_message_id(state_key)
        
        safe_category = sanitize(category_path)
        safe_channel = sanitize(channel_name)
        safe_filename = sanitize(file_name)
        
        # 構造: KNOWLEDGE_BASE / カテゴリ / チャンネル / ...
        base_dir = os.path.join(KNOWLEDGE_BASE_DIR, safe_category, safe_channel)

        if is_thread:
            channel_dir = os.path.join(base_dir, safe_filename)
        else:
            channel_dir = base_dir

        messages_dir = os.path.join(channel_dir, "messages")
        jsonl_file = os.path.join(channel_dir, "messages.jsonl")
        meta_file = os.path.join(channel_dir, "channel_info.json")
        attachments_dir = os.path.join(channel_dir, 'attachments')
        
        os.makedirs(channel_dir, exist_ok=True)
        os.makedirs(messages_dir, exist_ok=True)
        os.makedirs(attachments_dir, exist_ok=True)
        
        # --- メタデータの保存 ---
        if not os.path.exists(meta_file):
            metadata = {
                "id": messageable.id,
                "name": messageable.name,
                "type": str(messageable.type),
                "created_at": str(messageable.created_at) if hasattr(messageable, 'created_at') else None,
                "topic": getattr(messageable, 'topic', None),
                "category": category_path,
                "parent_channel": channel_name if is_thread else None,
                "is_thread": is_thread,
                "fetched_at": str(datetime.datetime.now())
            }
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=4, ensure_ascii=False)

        new_messages_count = 0
        
        try:
            async for message in messageable.history(limit=None, after=discord.Object(id=last_message_id) if last_message_id else None, oldest_first=True):
                
                await self.storage.add_message(message, attachments_dir, messages_dir, jsonl_file)
                
                new_messages_count += 1
                self.storage.update_last_message_id(state_key, message.id)

                if new_messages_count % 100 == 0:
                     logger.info(f"    ... これまでに {new_messages_count} 件のメッセージを処理しました")
            
            if new_messages_count > 0:
                logger.info(f'    {new_messages_count} 件の新しいメッセージを取得しました。')
                return True

        except discord.Forbidden:
             logger.warning(f'    アクセス拒否: {channel_name}/{file_name}')
        except Exception as e:
             logger.error(f'    取得エラー {channel_name}/{file_name}: {e}', exc_info=True)
        finally:
            # 残りのバッファを書き込み（エラー時も実行）
            self.storage.flush(messages_dir, jsonl_file)
             
        return False

def run_fetcher():
    if not DISCORD_TOKEN:
        logger.critical("エラー: .env に DISCORD_TOKEN が見つかりません")
        exit(1)

    intents = discord.Intents.default()
    intents.message_content = True
    intents.guilds = True 
    intents.members = True 
    
    client = DiscordFetcher(intents=intents)
    client.run(DISCORD_TOKEN)

if __name__ == '__main__':
    run_fetcher()

