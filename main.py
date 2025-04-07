import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import certifi

# 加載環境變量
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# 設置證書路徑
os.environ['SSL_CERT_FILE'] = certifi.where()

# 設置機器人前綴和意圖
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
bot = commands.Bot(command_prefix='!', intents=intents)

# 當機器人準備就緒時
@bot.event
async def on_ready():
    print(f'{bot.user} 已上線！')
    # 加載音樂 Cog
    try:
        await bot.load_extension('cogs.music')
        print('音樂模組已加載！')
    except Exception as e:
        print(f'加載音樂模組時發生錯誤: {str(e)}')
    # 加載 LLM 聊天 Cog
    try:
        await bot.load_extension('cogs.llm_chat')
        print('LLM 聊天模組已加載！')
    except Exception as e:
        print(f'加載 LLM 聊天模組時發生錯誤: {str(e)}')

# 重新加載命令
@bot.command()
@commands.has_permissions(administrator=True)
async def reload(ctx, module: str = None):
    """重新加載指定模組或所有模組（僅管理員可用）
    
    參數:
        module: 要重新加載的模組名稱（可選）。不指定則重新加載所有模組。
        例如: music, admin 等
    """
    try:
        if module:
            # 重新加載指定模組
            module_path = f'cogs.{module.lower()}'
            try:
                await bot.unload_extension(module_path)
            except commands.ExtensionNotLoaded:
                pass  # 如果未加載，忽略錯誤
            try:
                await bot.load_extension(module_path)
                await ctx.send(f"✅ 模組 '{module}' 已重新加載！")
            except Exception as e:
                await ctx.send(f"❌ 重新加載模組 '{module}' 時發生錯誤：{str(e)}")
        else:
            # 重新加載所有模組
            success = []
            failed = []
            
            # 獲取所有已加載的擴展
            extensions = list(bot.extensions.keys())
            
            # 重新加載每個擴展
            for ext in extensions:
                try:
                    await bot.reload_extension(ext)
                    success.append(ext.split('.')[-1])
                except Exception as e:
                    failed.append(f"{ext.split('.')[-1]} ({str(e)})")
            
            # 準備響應消息
            response = []
            if success:
                response.append(f"✅ 已重新加載的模組: {', '.join(success)}")
            if failed:
                response.append(f"❌ 重新加載失敗的模組: {', '.join(failed)}")
            
            await ctx.send('\n'.join(response) if response else "❌ 沒有找到可重新加載的模組")
            
    except Exception as e:
        print(f"重新加載時發生錯誤: {str(e)}")
        await ctx.send(f"❌ 重新加載時發生錯誤：{str(e)}")

# 錯誤處理
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ 您沒有權限執行此命令！")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ 找不到此命令！")
    else:
        print(f"命令執行錯誤: {str(error)}")
        await ctx.send(f"❌ 發生錯誤：{str(error)}")

# 運行機器人
bot.run(TOKEN)
