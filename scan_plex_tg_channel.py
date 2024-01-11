from telethon import TelegramClient, events
import requests
import os

# 从环境变量读取配置
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('BOT_TOKEN')
chat_id = os.getenv('CHAT_ID')
plex_token = os.getenv('PLEX_TOKEN')
plex_url = os.getenv('PLEX_URL')
libraries_config = os.getenv('LIBRARIES_CONFIG', '')  # 默认为空字符串
channel_username = os.getenv('CHANNEL_USERNAME', 'umziebook')  # 默认频道名

# 解析媒体库配置
libraries = {}
if libraries_config:
    for lib in libraries_config.split(','):
        lib_id, lib_name = lib.split(':')
        libraries[lib_id.strip()] = lib_name.strip()

def send_telegram_message(bot_token, chat_id, message):
    send_text = f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&parse_mode=Markdown&text={message}'
    response = requests.get(send_text)
    return response.json()

def scan_plex_libraries(plex_url, plex_token, libraries):
    for library_id, library_name in libraries.items():
        scan_message = f"📢 通知触发 Plex 扫库: {library_name}"
        send_telegram_message(bot_token, chat_id, scan_message)
        scan_url = f"{plex_url}/library/sections/{library_id}/refresh?X-Plex-Token={plex_token}"
        response = requests.get(scan_url)
        if response.status_code == 200:
            print(f"Plex 媒体库 '{library_name}' 扫描已启动")
        else:
            print(f"Plex 媒体库 '{library_name}' 扫描失败，错误码：{response.status_code}")

# 使用 Bot Token 启动客户端
client = TelegramClient('session_name', api_id, api_hash)
client.start(bot_token=bot_token)

print(f"成功连接到 Telegram。开始监测频道：{channel_username}")

@client.on(events.NewMessage(chats=channel_username))
async def new_message_listener(event):
    print("检测到新消息，触发 Plex 指定媒体库的扫描")
    scan_plex_libraries(plex_url, plex_token, libraries)

client.run_until_disconnected()
