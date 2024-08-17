# 参数说明
## bot_token 
请填写你的bot_token
## admin
列表 请填写可管理该bot的用户ID
## acc
列表 请填写用于link校验的账号stringsession
## bio_link_detect
False则不检测bio中的link acc为空时请保持False
## ocr_detect
todo 请保持false
## strict_mode
将文本转换成拼音与违禁词相比较，误杀概率较大，慎用 
## ban_words
违禁词列表

# 使用说明
填写好参数后安装依赖
pip3 install -r requirements.txt 
并直接python3 main.py即可

# 欢迎PR代码，Thx