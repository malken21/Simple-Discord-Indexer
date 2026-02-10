import logging
import os
import discord
from .utils import sanitize
from .config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

class MessageFormatter:
    """
    DiscordのメッセージオブジェクトをMarkdown形式などに変換するクラス
    """

    @staticmethod
    async def to_markdown(message: discord.Message, attachments_dir: str) -> str:
        """
        メッセージをMarkdown文字列に変換します。
        添付ファイルがあればダウンロード処理も行います（副作用あり）。
        TODO: 添付ファイルダウンロードの責務は分離すべきだが、現状はここで行う。
        """
        msg_content = ""

        # 著者ヘッダー
        author_name = message.author.display_name
        time_str = message.created_at.strftime('%H:%M')
        msg_content += f"### {author_name} ({time_str})\n"

        # 返信コンテキスト
        if message.reference:
                msg_content += f"> (Reply to message {message.reference.message_id})\n\n"

        # コンテンツ
        content = message.clean_content
        if content:
            msg_content += f"{content}\n\n"

        # 埋め込み (Embeds)
        for embed in message.embeds:
            if embed.title: msg_content += f"**Embed: {embed.title}**\n"
            if embed.description: msg_content += f"> {embed.description}\n"
            if embed.url: msg_content += f"[Link]({embed.url})\n"
            msg_content += "\n"

        # 添付ファイル
        if message.attachments:
            # attachments_dir が相対パスで渡されることを想定していないため
            # 呼び出し元で絶対パスを渡す必要があるが、Markdown内のリンクは相対パスにする必要がある
            # ここでは attachments_dir は物理的な保存先パスを受け取る
            
            for attachment in message.attachments:
                try:
                    safe_att_name = sanitize(attachment.filename)
                    filename = f"{message.id}_{safe_att_name}"
                    filepath = os.path.join(attachments_dir, filename)
                    
                    if not os.path.exists(filepath):
                        await attachment.save(filepath)
                    
                    # Markdownリンク（標準化された相対パス）
                    # ../attachments/{filename} という構造は固定とする
                    rel_path = f"../attachments/{filename}"
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                        msg_content += f"![{attachment.filename}]({rel_path})\n"
                    else:
                        msg_content += f"[{attachment.filename}]({rel_path})\n"
                except Exception as e:
                    logger.warning(f"    添付ファイルのダウンロードに失敗しました {attachment.filename}: {e}")
        
        msg_content += "\n" # メッセージ間のスペース
        return msg_content
