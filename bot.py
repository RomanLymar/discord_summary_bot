import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import datetime

# Завантаження змінних середовища
load_dotenv()

TOKEN = os.getenv('TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
IMPORTANT_ROLE = "Summary"

# Налаштування інтентів
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

# Ініціалізація бота
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Бот запущений як {bot.user}")

@bot.command()
async def digest(ctx):
    guild = bot.get_guild(GUILD_ID)
    summary_role = discord.utils.get(guild.roles, name=IMPORTANT_ROLE)
    if not summary_role:
        await ctx.send("Роль Summary не знайдена на сервері.")
        return

    now = datetime.datetime.utcnow()
    yesterday = now - datetime.timedelta(days=1)

    collected_messages = []

    for channel in guild.text_channels:
        try:
            async for message in channel.history(after=yesterday, oldest_first=True, limit=1000):
                if message.author.bot:
                    continue
                if summary_role in message.author.roles:
                    if not message.content.strip().startswith("!digest"):
                        collected_messages.append((channel.name, message))
        except Exception as e:
            print(f"Помилка при скануванні каналу {channel.name}: {e}")

    if collected_messages:
        today = now.strftime("%d.%m")
        yesterday_str = yesterday.strftime("%d.%m")
        title = f"Выжимка 2TOP SQUAD {yesterday_str}-{today}"

        embed = discord.Embed(
            title=title,
            color=discord.Color.blue()
        )

        for channel_name, msg in collected_messages:
            content_preview = msg.content.split('\n')[0][:100]
            if not content_preview:
                content_preview = "Без тексту (можливо тільки вкладення)"
            embed.add_field(
                name=f"#{channel_name} – {content_preview}",
                value=f"[Перейти до повідомлення]({msg.jump_url})",
                inline=False
            )

        await ctx.send(embed=embed)
    else:
        await ctx.send("ℹ️ Немає нових важливих повідомлень за останні 24 години.")

# Запуск бота
bot.run(TOKEN)
