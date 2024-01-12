from telethon import TelegramClient, events
import requests
import os
import schedule
import asyncio
import datetime

# 从环境变量读取配置
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('BOT_TOKEN')
chat_id = os.getenv('CHAT_ID')
plex_token = os.getenv('PLEX_TOKEN')
plex_url = os.getenv('PLEX_URL')
libraries_config = os.getenv('LIBRARIES_CONFIG', '')  # 默认为空字符串
channel_username = os.getenv('CHANNEL_USERNAME', 'umziebook')  # 默认频道名
scan_time = os.getenv('SCAN_TIME', '')  # 定时扫描时间

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

def scheduled_scan():
    print(f"定时扫描启动 - {datetime.datetime.now()}")
    scan_plex_libraries(plex_url, plex_token, libraries)

# 定时任务设置
if scan_time:
    schedule.every().day.at(scan_time).do(scheduled_scan)
    print(f"定时任务已开启：{scan_time}")
else:
    print("定时任务未开启")

# 使用 Bot Token 启动客户端
client = TelegramClient('session_name', api_id, api_hash)
client.start(bot_token=bot_token)

print("Telegram 已连接成功")
print(f"监控频道为 {channel_username}")
print(f"Plex 扫描目录为 {', '.join(libraries.values())}")

async def run_scheduled_tasks():
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)

client.loop.create_task(run_scheduled_tasks())

@client.on(events.NewMessage(chats=channel_username))
async def new_message_listener(event):
    print("检测到新消息，触发 Plex 指定媒体库的扫描")
    scan_plex_libraries(plex_url, plex_token, libraries)

client.run_until_disconnected()
