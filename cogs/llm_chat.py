import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

client = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

class LlmChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.model_name = "deepseek/deepseek-chat:free"

    @commands.Cog.listener()
    async def on_message(self, message):
        # 忽略自己的消息
        if message.author == self.bot.user:
            return

        # 如果機器人被提及
        if self.bot.user in message.mentions:
            # 去除提及機器人的部分
            content = message.content.replace(f'<@{self.bot.user.id}>', '').strip()
            if content:
                try:
                    response = await client.chat.completions.create(
                        model=self.model_name,
                        messages=[
                            {"role": "system", "content": "你是一個Discord音樂機器人助手。當且僅當用戶明確要求以下操作時，請輸出對應的 Discord 指令：\n"
                                                        "- 播放音樂：`!play 歌名`\n"
                                                        "- 跳過當前歌曲：`!skip`\n"
                                                        "- 暫停播放：`!pause`\n"
                                                        "- 繼續播放：`!resume`\n"
                                                        "- 停止播放並退出語音頻道：`!leave`\n"
                                                        "- 加入語音頻道：`!join`\n"
                                                        "其他任何情況下，請正常回覆用戶，不要輸出任何指令。不要輸出多餘的文字。"},
                            {"role": "user", "content": content}
                        ],
                        max_tokens=512,
                        temperature=0.7
                    )
                    # 調試打印完整回應
                    print(f"OpenRouter 回應: {response}")
                    # 檢查是否有錯誤
                    error = getattr(response, 'error', None)
                    if error:
                        msg = error.get('message', '未知錯誤')
                        code = error.get('code', '無代碼')
                        await message.channel.send(f"❌ OpenRouter 錯誤 (代碼 {code}): {msg}")
                    elif response and response.choices and len(response.choices) > 0:
                        choice = response.choices[0]
                        reply = choice.message.content.strip()
                        refusal = getattr(choice.message, 'refusal', None)
                        if refusal:
                            await message.channel.send(f"❌ 模型拒絕回應：{refusal}")
                        elif reply:
                            # 去除反引號
                            reply_clean = reply.replace('`', '').strip()
                            # 如果模型回應看起來像命令，則模擬用戶發送該命令
                            if reply_clean.startswith("/") or reply_clean.startswith("!"):
                                parts = reply_clean.lstrip("!/").split(maxsplit=1)
                                command_name = parts[0].lower()
                                arg_str = parts[1] if len(parts) > 1 else ""
                                # 嘗試獲取命令
                                command = self.bot.get_command(command_name)
                                if command:
                                    ctx = await self.bot.get_context(message)
                                    # 根據命令名稱決定是否傳參數
                                    if command_name == "play" and arg_str:
                                        await ctx.invoke(command, query=arg_str)
                                    else:
                                        await ctx.invoke(command)
                                else:
                                    await message.channel.send(f"❌ 找不到指令 `{command_name}`，請確認。")
                            else:
                                await message.channel.send(reply)
                        else:
                            await message.channel.send("❌ 模型未生成回應。")
                    else:
                        await message.channel.send("❌ 未獲得模型回應。")
                except Exception as e:
                    print(f"OpenRouter API 錯誤: {str(e)}")
                    await message.channel.send("❌ 發生錯誤，無法獲取回應。")
            else:
                await message.channel.send("請輸入內容。")

        # 確保命令仍然有效
        await self.bot.process_commands(message)

    @commands.command(name="model")
    async def change_model(self, ctx, *, model_name: str = None):
        """查詢或切換 LLM 模型"""
        if model_name:
            self.model_name = model_name.strip()
            await ctx.send(f"✅ 已切換模型為：`{self.model_name}`")
        else:
            await ctx.send(f"目前使用的模型是：`{self.model_name}`")

async def setup(bot):
    await bot.add_cog(LlmChatCog(bot))
