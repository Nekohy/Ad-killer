import json
import os

import plyvel
import random
import re
import string

from opentele.api import API
from opentele.tl import TelegramClient
from pypinyin import lazy_pinyin
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from telegram.ext import CallbackContext
from telethon.errors import UserDeactivatedBanError
from telethon.sessions import StringSession
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import CheckChatInviteRequest
from telethon.tl.types import User, Channel
from telegram.constants import ChatMemberStatus


class Userbot:
    def __init__(self, accs: list):
        self.accs = accs
        self.client = None

    async def __generate_random_string(self):
        letters = string.ascii_lowercase
        return ''.join(random.choices(letters, k=5))

    async def check_link(self, private, public):
        datas = []
        if not private and not public:
            return None
        elif private:
            for i in private:
                types = await self.client(CheckChatInviteRequest(i))
                datas.append(types.title)
                datas.append(types.about)
        elif public:
            for i in public:
                types = await self.client.get_entity(i)
                if isinstance(types, Channel):
                    datas.append(types.title)
                # todo 用户判断
                elif isinstance(types, User):
                    pass
        return str(datas)

    async def login(self):
        acc = random.randint(0, len(self.accs) - 1)
        session = self.accs[acc]
        api = API.TelegramDesktop.Generate(system="windows", unique_id=await self.__generate_random_string())
        try:
            self.client = TelegramClient(StringSession(session), api=api)
            await self.client.connect()
            return None
        except UserDeactivatedBanError:
            return acc
        except ValueError as e:
            return str(e)


class Bot:
    def __init__(self, update, context):
        self.update = update
        self.context = context
        self.chat_id = context.user_data["chat_id"]
        self.config = json.loads(db.get(str(self.chat_id).encode()).decode())
        self.keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("管理员列表", callback_data='admin')],
        [InlineKeyboardButton("账号列表", callback_data='userbot')],
        [InlineKeyboardButton("禁用词列表", callback_data='manage_ban_words')],
        [InlineKeyboardButton("切换简介链接检测", callback_data='toggle_bio_link_detect')],
        [InlineKeyboardButton("切换严格模式", callback_data='toggle_strict_mode')],
        [InlineKeyboardButton("关闭", callback_data='close')]
    ])

    async def get_user_info(self):
        message = self.update.message
        # 检查 /report 命令是否是回复某条消息
        if message.reply_to_message:
            reply_message = message.reply_to_message
            user_info = await self.context.bot.get_chat(reply_message.from_user.id)
            if user_info.photo and init_config["ocr_detect"]:
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
        return await self.context.bot.ban_chat_member(self.chat_id, userid, revoke_messages=True)

    async def is_admin(self, user_id):
        chat_member = await self.context.bot.get_chat_member(self.chat_id, user_id)
        if chat_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await self.update.message.reply_text("无法举报管理员/群主")
        elif chat_member.status in [ChatMemberStatus.BANNED, ChatMemberStatus.LEFT]:
            await self.update.message.reply_text("该用户已不在群里")
        else:
            return None
        return True
    async def menu(self):
        back = InlineKeyboardMarkup([[InlineKeyboardButton("返回主菜单", callback_data='main_menu')]])
        user = str(self.update.effective_user.id)
        query = self.update.callback_query
        if query:
            message = query.message
            data = query.data
        else:
            message = self.update.message
            data = 'main_menu'
        if str(user) not in str(self.config["admin"]):
            return await message.reply_text("您不在管理员名单内")
        if data == 'main_menu':
            if query:
                await query.answer()
                await query.edit_message_text('请选择要修改的设置：', reply_markup=self.keyboard)
            else:
                await message.reply_text('请选择要修改的设置：', reply_markup=self.keyboard)
            self.context.user_data['expect_input'] = None
        elif data == 'admin':
            await query.answer()
            accs_text = str(self.config['admin']) if self.config['admin'] else None
            await query.edit_message_text(f"当前管理员列表：\n{accs_text}\n\n请输入新的id列表，空格分隔：",
                                          reply_markup=back)
            self.context.user_data['expect_input'] = 'admin'
        elif data == 'userbot':
            await query.answer()
            accs_text = str(self.config['accs']) if self.config['accs'] else None
            await query.edit_message_text(f"当前账号列表：\n{accs_text}\n\n请输入新的id列表，空格分隔：",
                                          reply_markup=back)
            self.context.user_data['expect_input'] = 'accs'
        elif data == 'manage_ban_words':
            ban_words_text = ", ".join(self.config['ban_words'])
            await query.edit_message_text(f"当前禁用词：{ban_words_text}\n\n请输入新的禁用词列表，用逗号分隔：",
                                          reply_markup=back)
            self.context.user_data['expect_input'] = 'ban_words'
        elif data == 'toggle_bio_link_detect':
            self.config['bio_link_detect'] = not self.config['bio_link_detect']
            await query.answer(text=f"简介链接检测已{'开启' if self.config['bio_link_detect'] else '关闭'}",
                               show_alert=True)
        elif data == 'toggle_strict_mode':
            self.config['strict_mode'] = not self.config['strict_mode']
            await query.answer(f"严格模式已{'开启' if self.config['strict_mode'] else '关闭'}",
                                          show_alert=True)
        elif data == 'close':
            if query:
                await query.edit_message_text('修改完成')
            else:
                await message.reply_text('修改完成')
        db.put(str(self.chat_id).encode(),json.dumps(self.config).encode())
    # 处理用户输入
    async def input_params(self):
        if 'expect_input' not in self.context.user_data:
            return
        input_type = self.context.user_data['expect_input']
        del self.context.user_data['expect_input']
        if input_type == 'accs':
            self.config['accs'] = None if self.update.message.text is None else [acc.strip() for acc in self.update.message.text.split() if acc.strip()]
            await self.update.message.reply_text("账号列表已更新", reply_markup=self.keyboard)
        elif input_type == 'admin':
            self.config['admin'] = None if self.update.message.text is None else [acc.strip() for acc in self.update.message.text.split() if acc.strip()]
            await self.update.message.reply_text("账号列表已更新", reply_markup=self.keyboard)
        elif input_type == 'ban_words':
            self.config['ban_words'] = None if self.update.message.text is None else [word.strip() for word in self.update.message.text.split() if word.strip()]
            await self.update.message.reply_text("禁用词列表已更新", reply_markup=self.keyboard)
        db.put(str(self.chat_id).encode(), json.dumps(self.config).encode())

async def is_sublist_adjacent(sublist, mainlist):
    sub_len = len(sublist)
    for i in range(len(mainlist) - sub_len + 1):
        if mainlist[i:i + sub_len] == sublist:
            return True
    return None

async def process_ban_word(text):
    if not text:
        return None
    if init_config["strict_mode"]:
        for ban_word in init_config["ban_words"]:
            process_text = lazy_pinyin(text.replace(" ", ""))
            ban_pinyin = lazy_pinyin(ban_word)
            word_detect = await is_sublist_adjacent(process_text, ban_pinyin)
            if word_detect:
                break
    else:
        for ban_word in init_config["ban_words"]:
            if ban_word in text.replace(" ", ""):
                word_detect = True
                break
    return word_detect


async def process_link(text):
    if init_config["bio_link_detect"]:
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
    return private_links, public_groups


async def report(update: Update, context: CallbackContext):
    bot = Bot(update, context)
    text, user_id, bio, user_photo = await bot.get_user_info()
    if await bot.is_admin(user_id):
        return
    private_links, public_groups = await process_link(bio)
    word_detect = await process_ban_word(text)
    if word_detect:
        await bot.ban_user(user_id)
        return await update.message.reply_text(f"用户{user_id}已被封禁")
    if init_config["bio_link_detect"]:
        if init_config["accs"]:
            userbot = Userbot(init_config["accs"])
            return_code = await userbot.login()
            if isinstance(return_code, int):
                await update.message.reply_text(f"session{return_code}失效，已清除，请重新输入命令")
            elif isinstance(return_code, str):
                await update.message.reply_text(f"错误代码 {return_code}")
            else:
                check_result = await userbot.check_link(private_links, public_groups)
                result = await process_ban_word(check_result)
                if result:
                    await bot.ban_user(user_id)
                    return await update.message.reply_text(f"用户{user_id}已被封禁")
        else:
            await update.message.reply_text("当前无可用账号")
    return await update.message.reply_text(f"用户{user_id}未检测到违禁词")


# 处理菜单操作
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        context.user_data["chat_id"] = context.args[0]
    else:
        if update.effective_chat.type == "private" and not context.user_data["chat_id"]:
            return await update.message.reply_text("私聊状态下请在后面添加需要管理的群组id重试")
        elif update.effective_chat.type != "private":
            context.user_data["chat_id"] = update.effective_chat.id

    bot = Bot(update, context)
    await bot.menu()

async def init_params(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = Bot(update, context)
    await bot.input_params()

async def init(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_config = {
        "admin": [],
        "accs": [],
        "bio_link_detect": False,
        "strict_mode": False,
        "ocr_detect": False,
        "ban_words": []
    }
    chat_id = update.message.chat_id
    admin_origin_list = await context.bot.get_chat_administrators(chat_id)
    admin_id_list = []
    for admin in admin_origin_list:
        if admin.status == "creator":
            admin_id_list.append(admin.user.id)
    init_config['admin'] = admin_id_list
    db.put(str(chat_id).encode(), json.dumps(init_config).encode())
    await update.message.reply_text("初始化完成")

def main():
    application = Application.builder().token(bot_token).build()
    application.add_handler(CommandHandler("start", init))
    application.add_handler(CommandHandler("report", report))
    application.add_handler(CommandHandler("config", menu))
    application.add_handler(CallbackQueryHandler(menu))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, init_params))
    application.run_polling()


if __name__ == '__main__':
    db_path = './leveldb'
    init_config = {
        "admin": [],
        "accs": [],
        "bio_link_detect": False,
        "strict_mode": False,
        "ocr_detect": False,
        "ban_words": []
    }
    if not os.path.exists(db_path):
        bot_token = input("请输入您的bot_token: ")
        db = plyvel.DB('./leveldb', create_if_missing=True)
        db.put(b'bot_token', bot_token.encode())
    else:
        try:
            db = plyvel.DB(db_path)
            bot_token = db.get(b'bot_token').decode()
        except:
            ValueError("数据库可能已损坏")
    main()
