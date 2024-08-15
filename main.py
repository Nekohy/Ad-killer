import random
import re
import string

from opentele.api import API
from opentele.tl import TelegramClient
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext
from telethon.errors import UserDeactivatedBanError
from telethon.sessions import StringSession
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import CheckChatInviteRequest


class Userbot:
    def __init__(self, accs: dict):
        self.accs = accs
        self.client = None

    async def __generate_random_string(self):
        letters = string.ascii_lowercase
        return ''.join(random.choices(letters, k=5))

    async def __process_link(self):
        pass

    async def check_link(self):
        try:
            await self.client.catch_up()
            await self.client(CheckChatInviteRequest(link))
        except UserDeactivatedBanError:
            print("用户已被封禁")

    async def login(self):
        api = API.TelegramDesktop.Generate(system="windows", unique_id=await self.__generate_random_string())
        with TelegramClient(StringSession(), api) as client:
            return await client.session.save()


class Bot:
    def __init__(self, update, context):
        self.update = update
        self.context = context
        self.chat_id = update.effective_chat.id

    async def get_info(self):
        message = self.update.message
        # 检查 /report 命令是否是回复某条消息
        if message.reply_to_message:
            reply_message = message.reply_to_message
            user_info = await self.context.bot.get_chat(reply_message.from_user.id)
            if user_info.photo:
                file = await self.context.bot.get_file(user_info.photo.big_file_id)
                await file.download_to_drive(f'./temp/{user_info.id}.jpg')
                user_photo = f'./temp/{user_info.id}.jpg'
            else:
                user_photo = None
            return reply_message.text, user_info.id, user_info.bio, user_photo
        else:
            await self.update.message.reply_text("请回复要举报的消息")
            return None

    async def ban_user(self):
        pass


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


async def main(update: Update, context: CallbackContext):
    bot = Bot(update, context)
    text, user_id, bio, user_photo = await bot.get_info()
    link = await process_bio(bio)


# 创建应用实例
application = ApplicationBuilder().token(TOKEN).build()
# 添加处理器
application.add_handler(CommandHandler("report", main))
# 启动机器人
application.run_polling()
