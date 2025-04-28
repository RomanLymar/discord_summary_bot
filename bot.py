import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import datetime
import asyncio

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

# Функція для перевірки чи має автор роль Summary
def has_summary_role(member):
    return any(role.name == IMPORTANT_ROLE for role in member.roles)

# Подія при запуску бота
@bot.event
async def on_ready():
    print(f"✅ Бот запущений як {bot.user}")
    await fetch_recent_messages()
    daily_summary.start()

# Функція для збору історії повідомлень за останні 24 години
async def fetch_recent_messages():
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("Не знайдено сервер.")
        return

    now = datetime.datetime.utcnow()
    yesterday = now - datetime.timedelta(days=1)

    for channel in guild.text_channels:
        if not channel.permissions_for(guild.me).read_message_history:
            continue  # якщо бот не має прав читати історію, пропускаємо канал

        try:
            async for message in channel.history(after=yesterday, limit=None):
                if message.author.bot:
                    continue
                member = guild.get_member(message.author.id)
                if member and has_summary_role(member):
                    important_messages.append(message)
        except Exception as e:
            print(f"Помилка читання історії каналу {channel.name}: {e}")

# Обробка нових повідомлень у реальному часі
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    guild = bot.get_guild(GUILD_ID)
    member = guild.get_member(message.author.id)

    if member and has_summary_role(member):
        important_messages.append(message)

    await bot.process_commands(message)

# Автоматичне надсилання дайджеста о 6 ранку за Києвом
@tasks.loop(minutes=1)
async def daily_summary():
    now = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=3)  # Київ = UTC+3
    if now.hour == 6 and now.minute == 0:
        await send_digest()

# Функція надсилання дайджеста
async def send_digest():
    channel = bot.get_channel(CHANNEL_ID)
    if important_messages:
        today = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=3)
        yesterday = today - datetime.timedelta(days=1)

        embed = discord.Embed(
            title=f"📚 Выжимка 2TOP SQUAD {yesterday.strftime('%d.%m')}-{today.strftime('%d.%m')}",
            color=discord.Color.blue()
        )

        for msg in important_messages:
            content_preview = msg.content.split('\n')[0][:100]
            if content_preview.lower().startswith("!digest"):
                continue  # пропустити команду !digest

            if not content_preview:
                content_preview = "Без тексту (можливо тільки вкладення)"

            embed.add_field(
                name=f"#{msg.channel.name} – {content_preview}",
                value=f"[Перейти до повідомлення]({msg.jump_url})",
                inline=False
            )

        await channel.send(embed=embed)
        important_messages.clear()
    else:
        channel = bot.get_channel(CHANNEL_ID)
        await channel.send("ℹ️ Немає нових важливих повідомлень на цей момент.")

# Ручна команда для створення дайджеста
@bot.command()
async def digest(ctx):
    await send_digest()

# Запуск бота
bot.run(TOKEN)
