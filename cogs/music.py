import discord
from discord.ext import commands
import yt_dlp
from collections import deque
import asyncio

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = deque()
        self.volume = 0.5  # 默認音量 50%
        self.search_results = {}  # 用於存儲每個消息ID對應的搜索結果
        
    def format_duration(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    @commands.command()
    async def join(self, ctx):
        """加入語音頻道"""
        if not ctx.author.voice:
            await ctx.send("你必須先加入一個語音頻道！")
            return
            
        channel = ctx.author.voice.channel
        if ctx.voice_client:
            if ctx.voice_client.channel != channel:
                await ctx.voice_client.move_to(channel)
                await ctx.send(f"已移動到語音頻道：{channel.name}")
            else:
                await ctx.send(f"已經在語音頻道：{channel.name}")
        else:
            await channel.connect()
            await ctx.send(f"已加入語音頻道：{channel.name}")

    @commands.command()
    async def leave(self, ctx):
        """離開語音頻道"""
        if not ctx.voice_client:
            await ctx.send("我沒有在任何語音頻道中！")
            return
            
        channel_name = ctx.voice_client.channel.name
        await ctx.voice_client.disconnect()
        self.queue.clear()  # 清空播放隊列
        await ctx.send(f"已離開語音頻道：{channel_name}")

    @commands.command()
    async def play(self, ctx, *, query):
        """播放音樂"""
        if not ctx.author.voice:
            await ctx.send("請先加入一個語音頻道！")
            return

        channel = ctx.author.voice.channel
        if not ctx.voice_client:
            await channel.connect()
        elif ctx.voice_client.channel != channel:
            await ctx.voice_client.move_to(channel)

        await ctx.send("正在處理您的請求，請稍候...")

        try:
            ydl_opts = {
                'outtmpl': '%(title)s.%(ext)s',
                'default_search': 'auto',
                'format': 'bestaudio[acodec=aac]/bestaudio/best',
                'extractor_args': {
                    'youtube': {
                        'skip': ['dash', 'hls'],
                        'player_skip': ['webpage']
                    }
                },
                'max_downloads': 1,
                'no_warnings': True,
                'extract_flat': True,
                'no_check_certificates': True,
                'ignoreerrors': True,
                'no_color': True,
                'no_playlist': True,
                'no_check_formats': True,
                'quiet': True,
                'source_address': '0.0.0.0'
            }

            is_search = not query.startswith(('http://', 'https://', 'www.'))
            if is_search:
                query = f'ytsearch5:{query}'

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.cache.remove()
                info = ydl.extract_info(query, download=False)
                if info is None:
                    await ctx.send("無法獲取視頻信息，請檢查輸入是否正確。")
                    return

                if 'entries' in info:
                    search_results = []
                    for i, entry in enumerate(info['entries'], 1):
                        if entry:
                            title = entry.get('title', '未知標題')
                            duration = self.format_duration(entry.get('duration', 0))
                            search_results.append(f"{i}. {title} ({duration})")

                    result_message = "搜索結果：\n" + "\n".join(search_results)
                    result_message += "\n\n點擊下方表情符號選擇要播放的歌曲"
                    
                    message = await ctx.send(result_message)
                    self.search_results[str(message.id)] = info['entries']
                    
                    number_emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']
                    for i in range(min(len(info['entries']), 5)):
                        await message.add_reaction(number_emojis[i])
                    return

                if 'url' not in info:
                    await ctx.send("無法獲取音頻流，請稍後重試。")
                    return

                title = info.get('title', '未知標題')
                audio_url = info['url']
                
                self.queue.append((audio_url, title))

                if len(self.queue) == 1:
                    await self.play_next(ctx)
                else:
                    await ctx.send(f"已將 {title} 添加到隊列中！")

        except Exception as e:
            print(f"處理請求時發生錯誤: {str(e)}")
            await ctx.send(f"處理請求時發生錯誤：{str(e)}")

    async def play_next(self, ctx):
        if not self.queue:
            await ctx.send("隊列已空！")
            return

        if not ctx.voice_client or not ctx.voice_client.is_connected():
            try:
                channel = ctx.author.voice.channel
                await channel.connect()
            except Exception as e:
                print(f"重新連接時發生錯誤: {str(e)}")
                await ctx.send("無法連接到語音頻道，請稍後重試！")
                return

        try:
            current_song = self.queue[0]
            audio_url, title = current_song

            FFMPEG_OPTIONS = {
                'options': '-vn',
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
            }
            
            audio_source = discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS)
            transformed_source = discord.PCMVolumeTransformer(audio_source, volume=self.volume)
            
            def after_playing(error):
                if error:
                    print(f"播放時發生錯誤: {str(error)}")
                asyncio.run_coroutine_threadsafe(self.handle_song_end(ctx), self.bot.loop)

            ctx.voice_client.play(transformed_source, after=after_playing)
            await ctx.send(f"正在播放：{title} (音量: {int(self.volume * 100)}%)")
            
        except Exception as e:
            print(f"播放時發生錯誤: {str(e)}")
            await ctx.send(f"播放時發生錯誤：{str(e)}")
            if self.queue:
                self.queue.popleft()
            await self.handle_song_end(ctx)

    async def handle_song_end(self, ctx):
        if self.queue:
            self.queue.popleft()
        
        if self.queue:
            await self.play_next(ctx)
        else:
            await ctx.send("播放結束！")

    @commands.command()
    async def volume(self, ctx, vol: float = None):
        """設置音量 (0-200)"""
        if vol is None:
            await ctx.send(f"當前音量：{int(self.volume * 100)}%")
            return
            
        if not 0 <= vol <= 200:
            await ctx.send("音量必須在 0-200% 之間！")
            return
            
        self.volume = vol / 100
        
        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.volume = self.volume
            
        await ctx.send(f"音量已設置為 {int(vol)}%")

    @commands.command()
    async def skip(self, ctx):
        """跳過當前歌曲"""
        if not ctx.voice_client:
            await ctx.send("機器人未連接到語音頻道！")
            return
        
        if not ctx.voice_client.is_playing():
            await ctx.send("當前沒有正在播放的歌曲！")
            return
        
        ctx.voice_client.stop()
        await ctx.send("已跳過當前歌曲！")

    @commands.command(name='queue')
    async def queue_list(self, ctx):
        """查看播放隊列"""
        if not self.queue:
            await ctx.send("隊列為空！")
            return
        
        queue_list = "\n".join([f"{i+1}. {title}" for i, (_, title) in enumerate(self.queue)])
        await ctx.send(f"當前隊列：\n{queue_list}")

    @commands.command()
    async def clear(self, ctx):
        """清空播放隊列"""
        self.queue.clear()
        await ctx.send("已清空隊列！")

    @commands.command()
    async def pause(self, ctx):
        """暫停播放"""
        if not ctx.voice_client:
            await ctx.send("機器人未連接到語音頻道！")
            return
        
        if not ctx.voice_client.is_playing():
            await ctx.send("當前沒有正在播放的歌曲！")
            return
        
        ctx.voice_client.pause()
        await ctx.send("已暫停播放！")

    @commands.command()
    async def resume(self, ctx):
        """恢復播放"""
        if not ctx.voice_client:
            await ctx.send("機器人未連接到語音頻道！")
            return
        
        if not ctx.voice_client.is_paused():
            await ctx.send("當前沒有暫停的歌曲！")
            return
        
        ctx.voice_client.resume()
        await ctx.send("已恢復播放！")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """處理表情反應來選擇歌曲"""
        # 忽略機器人自己的反應
        if user.bot:
            return

        # 檢查是否是數字表情符號
        number_emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']
        if str(reaction.emoji) not in number_emojis:
            return

        # 檢查這個消息是否有相關的搜索結果
        message_id = str(reaction.message.id)
        if message_id not in self.search_results:
            return

        # 獲取選擇的索引和搜索結果
        index = number_emojis.index(str(reaction.emoji))
        search_results = self.search_results[message_id]

        # 檢查索引是否有效
        if not 0 <= index < len(search_results):
            return

        # 獲取選中的視頻信息
        selected_video = search_results[index]
        if not selected_video:
            return

        # 創建一個新的上下文來執行播放命令
        ctx = await self.bot.get_context(reaction.message)
        ctx.author = user  # 設置命令執行者為反應的用戶

        # 使用視頻 URL 播放
        video_url = f"https://youtu.be/{selected_video['id']}"
        await self.play(ctx, query=video_url)

        # 清理搜索結果
        del self.search_results[message_id]

    @commands.command()
    async def musichelp(self, ctx):
        """顯示音樂機器人的所有可用指令"""
        embed = discord.Embed(
            title="🎵 音樂機器人指令列表",
            description="以下是所有可用的音樂指令：",
            color=discord.Color.blue()
        )

        commands_info = {
            "基本指令": {
                "play <歌曲名稱或URL>": "播放音樂或將歌曲加入隊列",
                "join": "加入你當前的語音頻道",
                "leave": "離開語音頻道並清空隊列"
            },
            "播放控制": {
                "pause": "暫停當前播放",
                "resume": "恢復播放",
                "skip": "跳過當前歌曲",
                "volume <0-200>": "調整音量（預設50%）",
                "volume": "查看當前音量"
            },
            "隊列管理": {
                "queue": "顯示當前播放隊列",
                "clear": "清空播放隊列"
            }
        }

        for category, commands in commands_info.items():
            field_value = "\n".join([f"**!{cmd}**\n{desc}" for cmd, desc in commands.items()])
            embed.add_field(name=f"📑 {category}", value=field_value, inline=False)

        embed.set_footer(text="提示：使用 !play 時可以輸入關鍵字搜尋或直接貼上 YouTube 連結")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Music(bot)) 