def sanitize(name: str) -> str:
    """
    ファイル名またはディレクトリ名として安全に使用できるように文字列をサニタイズします。
    """
    return "".join(c for c in name if c.isalnum() or c in (' ', '-', '_', '.')).strip()

def replace_fake_uppercase(text: str) -> str:
    """
    '偽'の大文字（ホモグリフ）を標準のASCII大文字に置換します。
    """
    mapping = {
        "ꓮ": "A", "ꓐ": "B", "ꓚ": "C", "ꓓ": "D", "ꓰ": "E", "ꓝ": "F", "ꓖ": "G", "ꓧ": "H",
        "ꓲ": "I", "ꓙ": "J", "ꓗ": "K", "ꓡ": "L", "ꓟ": "M", "ꓠ": "N", "ꓳ": "O", "ꓑ": "P",
        "𝘘": "Q", "ꓣ": "R", "ꓢ": "S", "ꓔ": "T", "ꓴ": "U", "ꓦ": "V", "ꓪ": "W", "ꓫ": "X",
        "ꓬ": "Y", "ꓜ": "Z"
    }
    return "".join(mapping.get(c, c) for c in text)
