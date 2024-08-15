import asyncio
import re


async def process_bio(text):
    # 私有链接模式 - 修改为捕获组以便提取后半部分
    private_link_pattern = r'\b(?:https?://)?t\.me/\+([a-zA-Z0-9_-]+)'
    # 公有群组模式 - 修改以匹配更短的用户名
    public_group_pattern = r'@[a-zA-Z][a-zA-Z0-9_]{3,31}\b'
    # 邮箱地址模式 - 用于排除邮箱
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    # 首先移除所有邮箱地址
    text = re.sub(email_pattern, '', text)
    private_links = re.findall(private_link_pattern, text)
    public_groups = re.findall(public_group_pattern, text)
    if not private_links and not public_groups:
        return None
    return private_links, public_groups


text = """
这是一个包含 Telegram 链接的文本：
私有链接：t.me/+abcdefg123456
公有群组：@telegram_group
不应匹配的邮箱：example@gmail.com
另一个私有链接：https://t.me/+hijklmn789012
另一个公有群组：@nyco0721
一些无效的链接：t.me/noplus, @short
"""

print(asyncio.run(process_bio(text)))