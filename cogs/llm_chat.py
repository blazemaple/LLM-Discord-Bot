import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
from datetime import datetime, timezone, timedelta
import requests
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent, AgentType, Tool
from langchain.agents.agent import AgentOutputParser
from typing import Any, Dict

load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID')

class LlmChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chat_history = []
        self.last_music_command = None

        # 初始化 LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.7,
            streaming=False,
        )

        # 註冊 tools
        self.tools = []
        music_cmds = [
            ("play", self.play_tool, "播放音樂，參數為歌名。例如：play('Luther') 會輸出 '!play Luther'"),
            ("skip", self.skip_tool, "跳過當前歌曲，無需參數，會輸出 '!skip'"),
            ("pause", self.pause_tool, "暫停播放，無需參數，會輸出 '!pause'"),
            ("resume", self.resume_tool, "繼續播放，無需參數，會輸出 '!resume'"),
            ("leave", self.leave_tool, "停止播放並退出語音頻道，無需參數，會輸出 '!leave'"),
            ("join", self.join_tool, "加入語音頻道，無需參數，會輸出 '!join'"),
        ]
        for name, func, desc in music_cmds:
            self.tools.append(Tool(name=name, func=func, description=desc))
        self.tools.append(Tool(
            name="get_time",
            func=self.get_time,
            description="取得現在的台北時間，無需參數，會回傳格式化的時間字串。",
        ))
        self.tools.append(Tool(
            name="search_web",
            func=self.search_web,
            description="使用 Google 搜尋，參數為查詢關鍵字，會回傳前幾條摘要。",
        ))
        self.tools.append(Tool(
            name="summarize_url",
            func=self.summarize_url,
            description="摘要網址內容。參數可以是網址，或是'問題+網址'，會回傳該網址的網頁摘要，若有問題會一併附上。"
        ))

        # 加入 langchain 內建工具：維基百科、YahooFinanceNewsTool
        from langchain_community.tools import WikipediaQueryRun
        from langchain_community.utilities import WikipediaAPIWrapper
        try:
            from langchain_community.tools.yahoo_finance_news import YahooFinanceNewsTool
            self.tools.append(YahooFinanceNewsTool())
        except ImportError:
            pass  # 若未安裝 langchain_community，則略過
        self.tools.append(WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper()))

        # System prompt
        system_prompt = (
            "你是一個 Discord 多功能助手，可與用戶輕鬆聊天，支援文字、圖片、音樂、網路搜尋與網頁摘要。\n\n"
            "請根據用戶需求，正確選擇下列工具：\n"
            "- play：播放音樂，參數為歌名\n"
            "- skip：跳過當前歌曲\n"
            "- pause：暫停播放\n"
            "- resume：繼續播放\n"
            "- leave：停止播放並退出語音頻道\n"
            "- join：加入語音頻道\n"
            "- search_web：用於查詢關鍵字時，進行 Google 搜尋並整理多個網站摘要，並在回覆中附上參考來源網址\n"
            "- summarize_url：當用戶輸入網址或「問題+網址」時，請用此工具抓取該網頁內容並摘要，並附上原始問題\n"
            "- get_time：取得現在的台北時間\n\n"
            "特別注意：\n"
            "1. 當你發現用戶需求中有任何時間相關表達（如“今天”、“明天”、“後天”、“昨天”、“下週一”、“三天後”、“本月最後一天”等），請主動判斷其意義，並優先使用 get_time 工具將其轉換為具體日期，再將日期帶入 search_web 或其他相關工具進行查詢。\n"
            "2. 你可以理解多種自然語言時間表達，不僅限於固定關鍵字。\n"
            "3. 系統同時會自動兜底處理常見時間詞彙（如“今天”、“明天”等），但你仍應主動判斷並處理更複雜的時間需求。\n"
            "4. 遇到音樂、搜尋、網頁摘要等需求時，務必使用對應工具，不要直接用文字回覆。"
        )
        self.agent = initialize_agent(
            self.tools,
            self.llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True,
            agent_kwargs={"system_message": system_prompt}
        )

    # 音樂工具方法
    def play_tool(self, song: str = "") -> str:
        cmd = f"!play {song.strip()}" if song.strip() else "!play"
        self.last_music_command = cmd
        return cmd

    def skip_tool(self, _input: str = "") -> str:
        self.last_music_command = "!skip"
        return "!skip"

    def pause_tool(self, _input: str = "") -> str:
        self.last_music_command = "!pause"
        return "!pause"

    def resume_tool(self, _input: str = "") -> str:
        self.last_music_command = "!resume"
        return "!resume"

    def leave_tool(self, _input: str = "") -> str:
        self.last_music_command = "!leave"
        return "!leave"

    def join_tool(self, _input: str = "") -> str:
        self.last_music_command = "!join"
        return "!join"

    @staticmethod
    def get_time(_input: str = "") -> str:
        """取得現在的台北時間，無需參數，會回傳格式化的時間字串。"""
        tz = timezone(timedelta(hours=8))
        now = datetime.now(tz)
        return now.strftime("現在台北時間是 %Y-%m-%d %H:%M:%S")

    @staticmethod
    def summarize_url(query: str = "") -> str:
        """
        摘要網址內容。參數可以是網址，或是'問題+網址'，會回傳該網址的網頁摘要，若有問題會一併附上。
        """
        import re
        import requests
        from bs4 import BeautifulSoup

        def extract_text_from_url(url):
            headers = {
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                    '(KHTML, like Gecko) Chrome/120.0 Safari/537.36'
                ),
                'Referer': 'https://www.google.com',
                'Accept-Encoding': 'gzip, deflate',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                main_content = (
                    soup.find('main') or
                    soup.find('article') or
                    soup.find('div', {'id': 'content'}) or
                    soup.find('div', {'class': 'content'}) or
                    soup.body
                )
                for tag in main_content(['script', 'style', 'header', 'footer', 'nav', 'form', 'aside']):
                    tag.decompose()
                raw_text = main_content.get_text(separator='\n', strip=True)
                lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
                clean_text = '\n'.join(lines)
                return clean_text
            except Exception as e:
                return f"(無法擷取內容: {e})"

        url_pattern = re.compile(r"https?://[^\s]+")
        urls_in_query = url_pattern.findall(query)
        result_parts = []
        if urls_in_query:
            for url_ in urls_in_query:
                text = extract_text_from_url(url_)
                if text and not text.startswith("(無法擷取內容"):
                    # 不限制字數，直接回傳全部正文
                    result_parts.append(f"{url_}\n【網頁摘要】{text}")
                else:
                    result_parts.append(f"{url_}\n{text}")
            question_part = url_pattern.sub("", query).strip()
            if question_part:
                result_parts.insert(0, f"【原始問題】{question_part}")
            return "\n\n".join(result_parts)
        else:
            return "請提供網址，或是'問題+網址'。"

    @staticmethod
    def search_web(query: str = "") -> str:
        """
        使用 Google 搜尋，參數為查詢關鍵字，回傳前幾條摘要，並自動進入網站抓取正文摘要。
        搜尋到的網址會傳遞給 summarize_url 進行文字擷取，並傳到 LLM 分析。
        """
        if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
            return "未設定 GOOGLE_API_KEY 或 GOOGLE_CSE_ID，無法搜尋。"
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CSE_ID,
            "q": query,
            "num": 5,
            "hl": "zh-TW"
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code != 200:
                return f"搜尋失敗，狀態碼：{resp.status_code}"
            data = resp.json()
            items = data.get("items", [])
            if not items:
                return "未找到相關結果。"
            snippets = []
            for item in items:
                title = item.get("title", "")
                desc = item.get("snippet", "")
                url_ = item.get("link", "")
                if url_:
                    # 使用 summarize_url 擷取文字
                    summary = LlmChatCog.summarize_url(url_)
                    snippets.append(f"{title}\n{desc}\n{url_}\n【網頁摘要】{summary}")
            result_text = "\n\n".join(snippets)
            return result_text
        except Exception as e:
            return f"搜尋時發生錯誤：{str(e)}"

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if self.bot.user in message.mentions:
            content = message.content.replace(f'<@{self.bot.user.id}>', '').strip()
            
            # 檢查是否有圖片附件
            image_url = None
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.content_type and attachment.content_type.startswith("image/"):
                        image_url = attachment.url
                        break  # 只處理第一張圖片

            loop = asyncio.get_event_loop()
            try:
                async with message.channel.typing():
                    # 若有圖片，直接 vision
                    if image_url:
                        messages = [
                            {"role": "system", "content": "你是一個能夠理解圖片內容的 Discord 助手，請根據用戶的訊息和圖片進行回覆。"},
                            {"role": "user", "content": [
                                {"type": "text", "text": content},
                                {"type": "image_url", "image_url": {"url": image_url}}
                            ]}
                        ]
                        result = await loop.run_in_executor(
                            None, lambda: self.llm.invoke(messages)
                        )
                        response = result.content if hasattr(result, "content") else str(result)
                        self.chat_history.append({"role": "user", "content": messages[1]["content"]})
                        self.chat_history.append({"role": "assistant", "content": response})
                    # 3. 其他走 agent 工具鏈
                    else:
                        result = await loop.run_in_executor(
                            None, lambda: self.agent.invoke({"input": content, "chat_history": self.chat_history})
                        )
                        response = result["output"] if isinstance(result, dict) and "output" in result else str(result)
                        self.chat_history.append({"role": "user", "content": content})
                        self.chat_history.append({"role": "assistant", "content": response})
                    if len(self.chat_history) > 20:
                        self.chat_history = self.chat_history[-20:]
                executed = False
                # 自動執行音樂指令
                if self.last_music_command:
                    import re, inspect
                    cmd_line = self.last_music_command.replace('`', '').replace('\n', '').strip()
                    match = re.match(r"!(play|skip|pause|resume|leave|join)\b\s*(.*)", cmd_line, re.IGNORECASE)
                    if match:
                        command_name = match.group(1).lower()
                        arg_str = match.group(2).strip()
                        command = self.bot.get_command(command_name)
                        if command:
                            ctx = await self.bot.get_context(message)
                            play_params = list(inspect.signature(command.callback).parameters)
                            if command_name == "play" and arg_str:
                                if "query" in play_params:
                                    await ctx.invoke(command, query=arg_str)
                                else:
                                    await ctx.invoke(command, arg_str)
                            else:
                                await ctx.invoke(command)
                            executed = True
                        else:
                            await message.channel.send(f"❌ 找不到指令 `{command_name}`，請確認。")
                    self.last_music_command = None
                # 聊天历史
                self.chat_history.append({"role": "user", "content": content})
                self.chat_history.append({"role": "assistant", "content": response})
                if len(self.chat_history) > 20:
                    self.chat_history = self.chat_history[-20:]
                if not executed:
                    await message.channel.send(response)
            except Exception as e:
                await message.channel.send(f"❌ Agent 發生錯誤：{str(e)}")
        await self.bot.process_commands(message)

async def setup(bot):
    await bot.add_cog(LlmChatCog(bot))
