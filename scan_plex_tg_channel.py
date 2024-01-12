import logging
from telethon import TelegramClient, events
import requests
import os
import schedule
import asyncio
import datetime

# 设置日志记录
logging.basicConfig(level=logging.DEBUG)

# 从环境变量读取配置
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('BOT_TOKEN')
chat_id = os.getenv('CHAT_ID')
plex_token = os.getenv('PLEX_TOKEN')
plex_url = os.getenv('PLEX_URL')
libraries_config = os.getenv('LIBRARIES_CONFIG', '')  # 默认为空字符串
channel_username = os.getenv('CHANNEL_USERNAME')  # 需要用户设置
scan_time = os.getenv('SCAN_TIME')  # 定时扫描时间，用户可设置

# 解析媒体库配置
libraries = {}
if libraries_config:
    libraries = dict(lib.split(':') for lib in libraries_config.split(','))

def send_telegram_message(bot_token, chat_id, message):
    send_text = f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&parse_mode=Markdown&text={message}'
    response = requests.get(send_text)
    return response.json()

def scan_plex_libraries(plex_url, plex_token, libraries):
    for library_id, library_name in libraries.items():
        scan_url = f"{plex_url}/library/sections/{library_id}/refresh?X-Plex-Token={plex_token}"
        response = requests.get(scan_url)
        if response.status_code == 200:
            print(f"Plex 媒体库 '{library_name}' 扫描已启动。")
        else:
            print(f"Plex 媒体库 '{library_name}' 扫描失败，错误码：{response.status_code}。")

def scheduled_scan():
    print(f"定时扫描任务启动 - {datetime.datetime.now()}")
    scan_plex_libraries(plex_url, plex_token, libraries)

# 定时任务设置
if scan_time:
    schedule.every().day.at(scan_time).do(scheduled_scan)
    print(f"定时任务已开启：{scan_time}")
else:
    print("定时任务未开启。")

# 使用 Bot Token 启动客户端
client = TelegramClient('anon', api_id, api_hash)

async def start_telegram_client():
    print("Attempting to start Telegram client...")
    try:
        await asyncio.wait_for(client.start(bot_token=bot_token), timeout=30)
        print("Telegram client successfully connected.")
        
        # 检查用户是否授权
        if not await client.is_user_authorized():
            print("Telegram client is not authorized. Exiting...")
            return False
    except asyncio.TimeoutError:
        print("Telegram client connection timed out.")
        return False
    except Exception as e:
        print(f"Failed to start the Telegram client: {e}")
        return False

    return True

async def run_scheduled_tasks():
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            print(f"Error during scheduled task: {e}")
        await asyncio.sleep(1)

async def main():
    print("Starting main function.")
    if not await start_telegram_client():
        print("Exiting due to Telegram client failure.")
        return

    print("Telegram client started.")
    client.loop.create_task(run_scheduled_tasks())
    print("Scheduled tasks set up.")

    @client.on(events.NewMessage(chats=channel_username))
    async def new_message_listener(event):
        print("Detected new message, triggering Plex library scan.")
        scan_plex_libraries(plex_url, plex_token, libraries)

    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
