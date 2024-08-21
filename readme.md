# 用途
检测用户发送文字，名称，简介，

若额外配置User可检测简介内私有/公开群组的链接信息，

与关键词匹配（严格模式匹配拼音）并封禁用户
# todo
1.类型判断账号和管理员列表，并强制添加群主和有ban人权限的管理进入bot

~~2.给/start做鉴权~~，给带ban权限的管理一个身份

~~3.去除bio_link_detect~~

~~4.用query.answer来弹出界面而不是发送消息~~

5. 检测用户的大会员emoji表情

6. 补全OCR模块，添加对群组照片的处理
# 运行说明
填写好参数后安装依赖

pip3 install -r requirements.txt 

python3 main.py

初次使用请填写bot_token

并在群组内运行/start，默认给予群主管理权限

# 使用说明
若填写错误导致无法进入，可以运行/start

请使用 /report 回复需要举报的消息

在群组内可以使用 /config 唤出菜单（请注意隐藏重要信息）或在私聊内输入/config + 群组id(应为-100开头)

# 参数说明
## admin
列表 请填写可管理该bot的用户ID
## acc
列表 请填写用于link校验的账号stringsession（Telethon格式）若填写则会执行用户简介检测
## ocr_detect
todo 请保持false
## strict_mode
将文本转换成拼音与违禁词相比较，误杀概率较大，慎用 
## ban_words
违禁词列表
# 欢迎PR代码，Thx