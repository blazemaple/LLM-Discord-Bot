# LLM Discord 智能機器人

一個功能豐富的 LLM Discord 智能機器人，支持自然語言對話、網路搜尋、YouTube 音樂播放、搜索和隊列管理。

## ✨ 特色功能

- 🎵 YouTube 音樂播放和搜索
- 🔍 關鍵字搜索並通過表情符號選擇歌曲
- 📋 播放隊列管理
- 🎚️ 音量控制（0-200%）
- ⏯️ 播放控制（暫停/恢復/跳過）
- 🎯 直觀的指令系統

## 🔧 環境要求

- Python 3.12 或更高版本
- FFmpeg（系統級依賴）
- Discord Bot Token
- 以下 Python 包：
  - discord.py >= 2.3.2
  - python-dotenv >= 1.0.0
  - yt-dlp >= 2025.03.31
  - certifi >= 2025.1.31
  - PyNaCl >= 1.5.0

## 📦 安裝步驟

1. 安裝 FFmpeg：
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install ffmpeg

   # Windows（使用 chocolatey）
   choco install ffmpeg
   ```

2. 克隆專案：
   ```bash
   git clone https://github.com/blazemaple/LycoReco_Bot.git
   cd lycoreco_bot
   ```

3. 使用 uv 創建虛擬環境並安裝依賴：
   ```bash
   uv venv
   source .venv/bin/activate  # Linux/macOS
   # 或
   .venv\Scripts\activate  # Windows
   
   uv pip install -r requirements.txt
   ```

4. 創建 `.env` 文件並設置 Token：
   ```
   DISCORD_TOKEN=你的機器人Token
   GOOGLE_API_KEY=你的GOOGLE API金鑰
   GOOGLE_CSE_ID=你的Google Search Engine ID
   ```

5. 執行：
   ```
   python main.py
   ```

## 🎮 使用方法

### 基本指令
- `!play <歌曲名稱或URL>` - 播放音樂或將歌曲加入隊列
- `!join` - 加入你當前的語音頻道
- `!leave` - 離開語音頻道並清空隊列

### 播放控制
- `!pause` - 暫停當前播放
- `!resume` - 恢復播放
- `!skip` - 跳過當前歌曲
- `!volume <0-200>` - 調整音量（預設50%）
- `!volume` - 查看當前音量

### 隊列管理
- `!queue` - 顯示當前播放隊列
- `!clear` - 清空播放隊列

### 幫助
- `!musichelp` - 顯示所有可用的音樂指令

## 🔍 搜索功能說明

使用 `!play` 指令搜索音樂時：
1. 輸入關鍵字，機器人會返回前5個搜索結果
2. 使用表情符號（1️⃣-5️⃣）選擇要播放的歌曲
3. 機器人會自動播放所選歌曲或將其加入隊列

### 網頁摘要功能

- 使用 `summarize_url` 方法，機器人會自動擷取網頁內容並生成摘要。
- 搜尋功能 `search_web` 現在完全依賴 `summarize_url` 來處理搜尋到的網址，確保摘要的一致性與準確性。
- 支援多語言網頁的摘要擷取，並自動過濾無關內容。

## 🛠️ 故障排除

1. 如果音樂無法播放：
   - 確保 FFmpeg 已正確安裝
   - 檢查機器人是否有適當的權限
   - 確認網絡連接正常

2. 如果機器人無法加入語音頻道：
   - 確保機器人有"連接"和"說話"權限
   - 檢查語音頻道是否已滿

3. 如果搜索功能無法使用：
   - 確保 yt-dlp 版本是最新的
   - 檢查網絡連接是否正常

## 📝 注意事項

- 建議使用穩定的網絡連接
- 音量調整範圍為 0-200%，預設為 50%
- 機器人需要適當的 Discord 權限才能正常運作
- 建議定期更新依賴包以獲得最佳體驗

## 🤖 LLM 聊天與自然語言控制

本機器人整合了大型語言模型（LLM），支援自然語言對話與控制音樂播放。

### 功能特色
- 直接 @提及機器人，輸入自然語言即可對話
- 自然語言指令自動轉換為音樂控制命令
- 支援：
  - 播放音樂：「幫我播放 Not Like Us」
  - 跳過歌曲：「跳過這首」
  - 暫停播放：「暫停音樂」
  - 繼續播放：「繼續播放」
  - 停止播放：「停止音樂」
  - 加入語音：「加入語音頻道」
- 無需輸入 `!play`、`!skip` 等命令，機器人會自動識別並執行

## 🔄 更新日誌

### 最新版本
- 新增表情符號選擇功能
- 優化音樂搜索體驗
- 改進錯誤處理機制
- 新增 musichelp 指令
- **整合 LLM 聊天與自然語言控制音樂功能**
- **網頁搜索功能**

## 貢獻

歡迎提交 Issue 和 Pull Request！

## 授權

MIT License
