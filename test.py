import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# 初始配置
config = {
    "bot_token": "",
    "accs": [],
    "bio_link_detect": False,
    "strict_mode": False,
    "ban_words": []
}


def load_config():
    global config
    with open("config.json", 'r', encoding='utf-8') as f:
        config = json.load(f)


# 保存配置到文件
def save_config():
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


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
    elif data == 'set_bot_token':
        await query.edit_message_text("请输入新的 Bot Token:", reply_markup=back)
        context.user_data['expect_input'] = 'bot_token'
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
    if input_type == 'bot_token':
        config['bot_token'] = update.message.text
        await update.message.reply_text("Bot Token 已更新", reply_markup=init_keyboard)
    elif input_type == 'accs':
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
        [InlineKeyboardButton("设置 Bot Token", callback_data='set_bot_token')],
        [InlineKeyboardButton("管理账号列表", callback_data='manage_accs')],
        [InlineKeyboardButton("切换生物链接检测", callback_data='toggle_bio_link_detect')],
        [InlineKeyboardButton("切换严格模式", callback_data='toggle_strict_mode')],
        [InlineKeyboardButton("管理禁用词", callback_data='manage_ban_words')],
        [InlineKeyboardButton("关闭", callback_data='close')]
    ])
    main()
