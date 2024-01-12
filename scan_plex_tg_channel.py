import logging
import requests
import os
import schedule
import asyncio
import datetime
from telethon import TelegramClient, events

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
session_file = os.getenv('SESSION_FILE')  # Telegram 会话文件的路径

# 确保session文件存在
if not session_file or not os.path.exists(session_file):
    logging.error("Session file is required but not found. Exiting...")
    exit(1)

# 解析媒体库配置
libraries = {}
if libraries_config:
    for lib in libraries_config.split(','):
        lib_id, lib_name = lib.split(':')
        libraries[lib_id.strip()] = lib_name.strip()

# 发送Telegram消息的函数
def send_telegram_message(bot_token, chat_id, message):
    send_text = f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&parse_mode=Markdown&text={message}'
    response = requests.get(send_text)
    return response.json()

# 扫描Plex媒体库的函数
def scan_plex_libraries(plex_url, plex_token, libraries):
    for library_id, library_name in libraries.items():
        scan_url = f"{plex_url}/library/sections/{library_id}/refresh?X-Plex-Token={plex_token}"
        response = requests.get(scan_url)
        if response.status_code == 200:
            logging.info(f"Plex 媒体库 '{library_name}' 扫描已启动。")
        else:
            logging.error(f"Plex 媒体库 '{library_name}' 扫描失败，错误码：{response.status_code}。")

# 定时扫描的函数
async def scheduled_scan():
    logging.info(f"定时扫描任务启动 - {datetime.datetime.now()}")
    scan_plex_libraries(plex_url, plex_token, libraries)

# 设置定时任务
if scan_time:
    schedule.every().day.at(scan_time).do(lambda: asyncio.create_task(scheduled_scan()))
    logging.info(f"定时任务已设置：{scan_time}")
else:
    logging.info("未设置定时任务。")

# 创建并启动Telegram客户端
client = TelegramClient(session_file, api_id, api_hash)

# 监听新消息事件
@client.on(events.NewMessage(chats=channel_username))
async def new_message_listener(event):
    print('有新消息！')
    logging.info("检测到新消息，触发Plex库扫描。")
    message = '检测到新消息，开始执行Plex库扫描。'
    send_telegram_message(bot_token, chat_id, message)
    await asyncio.create_task(scheduled_scan())

# 执行脚本的主要部分
async def main():
    await client.start()
    logging.info("Telegram客户端启动。")

    # 启动定时任务
    client.loop.create_task(run_scheduled_tasks())

    # 运行直到断开连接
    await client.run_until_disconnected()

# 运行定时任务的异步函数
async def run_scheduled_tasks():
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)

# 执行主函数
if __name__ == '__main__':