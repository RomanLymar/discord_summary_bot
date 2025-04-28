import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import datetime

# Завантаження змінних середовища
load_dotenv()

TOKEN = os.getenv('TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
IMPORTANT_ROLE = "Summary"

# Налаштування інтентів
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

# Ініціалізація бота
bot = commands.Bot(command_prefix="!", intents=intents)

# Список важливих повідомлень
important_messages = []

# Коли бот готовий
@bot.event
async def on_ready():
    print(f"✅ Бот запущений як {bot.user}")
    await fetch_recent_messages()
    daily_summary.start()

# Сканувати повідомлення за останні 24 години при запуску
async def fetch_recent_messages():
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("Guild not found!")
        return

    now = datetime.datetime.utcnow()
    yesterday = now - datetime.timedelta(days=1)

    for channel in guild.text_channels:
        try:
            async for message in channel.history(after=yesterday, oldest_first=True):
                if should_collect_message(guild, message):
                    important_messages.append(message)
        except (discord.Forbidden, discord.HTTPException) as e:
            print(f"❌ Не вдалося прочитати канал {channel.name}: {e}")

# Фільтрація повідомлень: тільки від учасників із потрібною роллю, без команд
def should_collect_message(guild, message):
    if message.author.bot:
        return False
    if message.content.startswith('!'):
        return False

    member = guild.get_member(message.author.id)
    if not member:
        return False

    role_names = [role.name for role in member.roles]
    return IMPORTANT_ROLE in role_names

# Ловити нові повідомлення після запуску
@bot.event
async def on_message(message):
    if should_collect_message(bot.get_guild(GUILD_ID), message):
        important_messages.append(message)

    await bot.process_commands(message)

# Команда вручну викликати дайджест
@bot.command()
async def digest(ctx):
    if important_messages:
        embed = discord.Embed(
            title="📚 Дайджест важливих повідомлень (ручний запуск)",
            color=discord.Color.blue()
        )

        for msg in important_messages:
            content_preview = msg.content.split('\n')[0][:100]
            if not content_preview:
                content_preview = "Без тексту (можливо тільки вкладення)"

            embed.add_field(
                name=f"#{msg.channel.name} – {content_preview}",
                value=f"[Перейти до повідомлення]({msg.jump_url})",
                inline=False
            )

        await ctx.send(embed=embed)
    else:
        await ctx.send("ℹ️ Немає нових важливих повідомлень на цей момент.")

# Автоматичний щоденний дайджест
@tasks.loop(time=datetime.time(hour=10, minute=0))
async def daily_summary():
    channel = bot.get_channel(CHANNEL_ID)
    if important_messages:
        embed = discord.Embed(
            title="📚 Щоденний дайджест важливих повідомлень",
            color=discord.Color.green()
        )

        for msg in important_messages:
            content_preview = msg.content.split('\n')[0][:100]
            if not content_preview:
                content_preview = "Без тексту (можливо тільки вкладення)"

            embed.add_field(
                name=f"#{msg.channel.name} – {content_preview}",
                value=f"[Перейти до повідомлення]({msg.jump_url})",
                inline=False
            )

        await channel.send(embed=embed)
        important_messages.clear()

# Запуск бота
bot.run(TOKEN)
