import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import yt_dlp
import asyncio

# 加載環境變量
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# 設置機器人前綴和意圖
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# 音樂隊列
queue = []

# 當機器人準備就緒時
@bot.event
async def on_ready():
    print(f'{bot.user} 已上線！')

# 播放音樂命令
@bot.command()
async def play(ctx, *, url):
    # 檢查用戶是否在語音頻道中
    if not ctx.author.voice:
        await ctx.send("請先加入一個語音頻道！")
        return

    # 加入語音頻道
    channel = ctx.author.voice.channel
    if not ctx.voice_client:
        await channel.connect()
    elif ctx.voice_client.channel != channel:
        await ctx.voice_client.move_to(channel)

    # 使用yt-dlp獲取音頻信息
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            url2 = info['url']
            title = info['title']
            
            # 添加到隊列
            queue.append((url2, title))
            
            if len(queue) == 1:
                await play_next(ctx)
            else:
                await ctx.send(f"已將 {title} 添加到隊列中！")
                
        except Exception as e:
            await ctx.send(f"發生錯誤：{str(e)}")

# 播放下一首歌曲
async def play_next(ctx):
    if not queue:
        return

    url, title = queue[0]
    
    # 播放音頻
    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }
    
    ctx.voice_client.play(
        discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS),
        after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
    )
    
    await ctx.send(f"正在播放：{title}")
    queue.pop(0)

# 跳過當前歌曲
@bot.command()
async def skip(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("已跳過當前歌曲！")
    else:
        await ctx.send("目前沒有在播放音樂！")

# 停止播放並清空隊列
@bot.command()
async def stop(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
    queue.clear()
    await ctx.send("已停止播放並清空隊列！")

# 顯示隊列
@bot.command()
async def queue_list(ctx):
    if not queue:
        await ctx.send("隊列為空！")
        return
    
    message = "當前隊列：\n"
    for i, (_, title) in enumerate(queue, 1):
        message += f"{i}. {title}\n"
    
    await ctx.send(message)

# 斷開連接
@bot.command()
async def disconnect(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("已斷開連接！")
    else:
        await ctx.send("機器人不在語音頻道中！")

# 運行機器人
bot.run(TOKEN) 