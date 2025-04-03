# Discord 音樂機器人

這是一個使用 Python 開發的 Discord 音樂機器人，可以播放 YouTube 音樂。

## 功能特點

- 播放 YouTube 音樂
- 支持音樂隊列
- 可以跳過當前歌曲
- 顯示當前隊列
- 支持斷開連接

## 安裝要求

- Python 3.8 或更高版本
- FFmpeg
- 以下 Python 包：
  - discord.py
  - python-dotenv
  - yt-dlp
  - PyNaCl

## 安裝步驟

1. 克隆此倉庫
2. 安裝依賴：
   ```
   pip install -r requirements.txt
   ```
3. 安裝 FFmpeg（如果尚未安裝）
4. 創建 `.env` 文件並添加你的 Discord 機器人令牌：
   ```
   DISCORD_TOKEN=你的機器人令牌
   ```

## 使用方法

- `!play [YouTube URL]` - 播放音樂
- `!skip` - 跳過當前歌曲
- `!stop` - 停止播放並清空隊列
- `!queue_list` - 顯示當前隊列
- `!disconnect` - 斷開機器人連接

## 注意事項

- 確保機器人有足夠的權限
- 使用前請確保已加入語音頻道
- 建議使用穩定的網絡連接 