import json
import random
import re
import string

import aiofiles
from opentele.api import API
from opentele.tl import TelegramClient
from pypinyin import lazy_pinyin
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from telegram.ext import CallbackContext
from telethon import functions
from telethon.errors import UserDeactivatedBanError
from telethon.sessions import StringSession
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import CheckChatInviteRequest


class Userbot:
    def __init__(self, accs: list):
        self.accs = accs
        self.client = None

    async def __generate_random_string(self):
        letters = string.ascii_lowercase
        return ''.join(random.choices(letters, k=5))

    async def check_link(self, private, public):
        await self.client.catch_up()
        if not private and not public:
            return None
        elif private:
            private = await self.client(CheckChatInviteRequest(private))
        elif public:
            await self.client(functions.channels.GetChannelsRequest(
                id=[public]
            ))

    async def login(self):
        acc = random.randint(0, len(self.accs))
        session = self.accs[acc]
        api = API.TelegramDesktop.Generate(system="windows", unique_id=await self.__generate_random_string())
        try:
            self.client = TelegramClient(StringSession(session), api)
            await self.client.connect()
            return False
        except UserDeactivatedBanError:
            return acc




class Bot:
    def __init__(self, update, context):
        self.update = update
        self.context = context
        self.chat_id = update.effective_chat.id

    async def get_user_info(self):
        message = self.update.message
        # 检查 /report 命令是否是回复某条消息
        if message.reply_to_message:
            reply_message = message.reply_to_message
            user_info = await self.context.bot.get_chat(reply_message.from_user.id)
            if user_info.photo and config["ocr_detect"]:
                file = await self.context.bot.get_file(user_info.photo.big_file_id)
                await file.download_to_drive(f'./temp/{user_info.id}.jpg')
                user_photo = f'./temp/{user_info.id}.jpg'
            else:
                user_photo = None
            return reply_message.text, user_info.id, user_info.bio, user_photo
        else:
            await self.update.message.reply_text("请回复要举报的消息")
            return None

    async def ban_user(self, userid):
        self.update.message.reply_text(f"已封禁用户 tg://openmessage?user_id={userid}")
        return self.update.ban_chat_member(self.chat_id, userid, revoke_messages=True)


async def read_json(path):
    async with aiofiles.open(path, "r") as f:
        data = await f.read()
        json_data = json.loads(data)
    return json_data["bot_token"], json_data["accs"], json_data["bio_link_detect"], json_data["strict_mode"], json_data[
        "ban_words"]


async def is_sublist_adjacent(sublist, mainlist):
    sub_len = len(sublist)
    for i in range(len(mainlist) - sub_len + 1):
        if mainlist[i:i + sub_len] == sublist:
            return True
    return False


def load_config():
    global config
    with open("config.json", 'r', encoding='utf-8') as f:
        config = json.load(f)


# 保存配置到文件
def save_config():
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


async def process_bio(text):
    word_detect = private_links = public_groups = None
    if config["strict_mode"]:
        for ban_word in config["ban_words"]:
            ban_pinyin = lazy_pinyin(ban_word)
            word_detect = await is_sublist_adjacent(lazy_pinyin(text.replace(" ", "")), ban_pinyin)
            if word_detect:
                break
    else:
        for ban_word in config["ban_words"]:
            if ban_word in text:
                word_detect = True
                break
    if config["bio_link_detect"]:
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
    return private_links, public_groups, word_detect


async def report(update: Update, context: CallbackContext):
    bot = Bot(update, context)
    text, user_id, bio, user_photo = await bot.get_user_info()
    private_links, public_groups, word_detect = await process_bio(bio)
    if word_detect:
        await bot.ban_user(user_id)
    if config["bio_link_detect"]:
        if config["accs"]:
            userbot = Userbot(config["accs"])
            num = await userbot.login()
            if num:
                await update.message.reply_text(f"session{num}失效，已清除，请重新输入命令")
            else:
                await userbot.check_link(private_links, public_groups)
        else:
            await update.message.reply_text("当前无可用账号")


# 处理菜单操作
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    back = InlineKeyboardMarkup([[InlineKeyboardButton("返回主菜单", callback_data='main_menu')]])
    query = update.callback_query
    if query:
        await query.answer()
        data = query.data
    else:
        message = update.message
        data = 'main_menu'
    if data == 'main_menu':
        if query:
            await query.edit_message_text('请选择要修改的设置：', reply_markup=init_keyboard)
        else:
            await message.reply_text('请选择要修改的设置：', reply_markup=init_keyboard)
    elif data == 'manage_accs':
        accs_text = "\n".join(config['accs'])
        await query.edit_message_text(f"当前账号列表：\n{accs_text}\n\n请输入新的账号列表，每行一个账号：",
                                      reply_markup=back)
        context.user_data['expect_input'] = 'accs'
    elif data == 'toggle_bio_link_detect':
        config['bio_link_detect'] = not config['bio_link_detect']
        await query.edit_message_text(f"简介链接检测已{'开启' if config['bio_link_detect'] else '关闭'}",
                                      reply_markup=back)
        save_config()
    elif data == 'toggle_strict_mode':
        config['strict_mode'] = not config['strict_mode']
        await query.edit_message_text(f"严格模式已{'开启' if config['strict_mode'] else '关闭'}",
                                      reply_markup=back)
        save_config()
    elif data == 'manage_ban_words':
        ban_words_text = ", ".join(config['ban_words'])
        await query.edit_message_text(f"当前禁用词：{ban_words_text}\n\n请输入新的禁用词列表，用逗号分隔：",
                                      reply_markup=back)
        context.user_data['expect_input'] = 'ban_words'
    elif data == 'close':
        if query:
            await query.edit_message_text('修改完成')
        else:
            await message.reply_text('修改完成')


# 处理用户输入
async def input_params(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'expect_input' not in context.user_data:
        return
    input_type = context.user_data['expect_input']
    del context.user_data['expect_input']
    if input_type == 'accs':
        config['accs'] = [acc.strip() for acc in update.message.text.split('\n') if acc.strip()]
        await update.message.reply_text("账号列表已更新", reply_markup=init_keyboard)
    elif input_type == 'ban_words':
        config['ban_words'] = [word.strip() for word in update.message.text.split(',') if word.strip()]
        await update.message.reply_text("禁用词列表已更新", reply_markup=init_keyboard)

    save_config()


def main():
    load_config()
    application = Application.builder().token(config['bot_token']).build()
    application.add_handler(CommandHandler("report", report))
    application.add_handler(CommandHandler("init", menu))
    application.add_handler(CallbackQueryHandler(menu))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, input_params))
    application.run_polling()


if __name__ == '__main__':
    init_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("管理账号列表", callback_data='manage_accs')],
        [InlineKeyboardButton("切换生物链接检测", callback_data='toggle_bio_link_detect')],
        [InlineKeyboardButton("切换严格模式", callback_data='toggle_strict_mode')],
        [InlineKeyboardButton("管理禁用词", callback_data='manage_ban_words')],
        [InlineKeyboardButton("关闭", callback_data='close')]
    ])
    config = {
        "bot_token": "",
        "accs": [],
        "bio_link_detect": False,
        "strict_mode": False,
        "ocr_detect": False,
        "ban_words": []
    }
    main()
