# 使用官方 Python 基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制脚本到容器中
COPY scan_plex_tg_channel.py .

# 安装 telethon
RUN pip install --no-cache-dir telethon requests schedule

# 运行脚本
CMD ["python", "scan_plex_tg_channel.py"]
