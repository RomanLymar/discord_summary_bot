import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import datetime
import pytz

# Завантаження змінних середовища
load_dotenv()

TOKEN = os.getenv('TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
SUMMARY_ROLE_ID = int(os.getenv('SUMMARY_ROLE_ID'))  # ID ролі @Summary

# Налаштування інтентів
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

# Ініціалізація бота
bot = commands.Bot(command_prefix="!", intents=intents)

# Список важливих повідомлень
important_messages = []

# Подія при запуску бота
@bot.event
async def on_ready():
    print(f"✅ Бот запущений як {bot.user}")
    daily_summary.start()

# Обробка нових повідомлень
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Ігнорувати команду !digest, щоб вона не потрапила у дайджест
    if message.content.startswith('!digest'):
        await bot.process_commands(message)
        return

    # Перевірка, чи є у повідомленні згадка ролі Summary
    if f"<@&{SUMMARY_ROLE_ID}>" in message.content:
        important_messages.append(message)

    await bot.process_commands(message)

# Формування дайджесту
async def send_digest(channel):
    if important_messages:
        # Встановити часову зону Києва
        kyiv_tz = pytz.timezone('Europe/Kyiv')
        now = datetime.datetime.now(kyiv_tz)
        yesterday = now - datetime.timedelta(days=1)
        title = f"📚 Выжимка 2TOP SQUAD {yesterday.strftime('%d.%m')}-{now.strftime('%d.%m')}"

        embed = discord.Embed(
            title=title,
            color=discord.Color.blue()
        )

        for msg in important_messages:
            # Отримати назву каналу
            channel_name = msg.channel.name
            content_preview = msg.content.split('\n')[0][:100]
            if not content_preview:
                content_preview = "Без тексту (можливо тільки вкладення)"

            embed.add_field(
                name=f"#{channel_name} – {content_preview}",
                value=f"[Перейти до повідомлення]({msg.jump_url})",
                inline=False
            )

        await channel.send(embed=embed)
        important_messages.clear()
    else:
        await channel.send("ℹ️ Немає нових важливих повідомлень на цей момент.")

# Ручна команда для надсилання дайджеста
@bot.command()
async def digest(ctx):
    channel = bot.get_channel(CHANNEL_ID)
    await send_digest(channel)

# Автоматичне надсилання дайджеста щодня о 6:00 за Києвом
@tasks.loop(minutes=1)
async def daily_summary():
    kyiv_tz = pytz.timezone('Europe/Kyiv')
    now = datetime.datetime.now(kyiv_tz)

    if now.hour == 6 and now.minute == 0:
        channel = bot.get_channel(CHANNEL_ID)
        await send_digest(channel)

# Запуск бота
bot.run(TOKEN)
