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
SUMMARY_ROLE_ID = int(os.getenv('SUMMARY_ROLE_ID'))

# Ініціалізація бота
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Список важливих повідомлень
important_messages = []

# Коли бот готовий
@bot.event
async def on_ready():
    print(f"✅ Бот запущений як {bot.user}")
    daily_summary.start()

# Обробка повідомлень
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    summary_mention = f"<@&{SUMMARY_ROLE_ID}>"

    if summary_mention in message.content:
        important_messages.append(message)

    await bot.process_commands(message)

# Функція для надсилання дайджесту
async def send_summary(channel):
    if important_messages:
        today = datetime.datetime.now(pytz.timezone('Europe/Kyiv'))
        yesterday = today - datetime.timedelta(days=1)

        embed = discord.Embed(
            title=f"📚 Выжимка 2TOP SQUAD {yesterday.strftime('%d.%m')}-{today.strftime('%d.%m')}",
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

        await channel.send(embed=embed)
        important_messages.clear()
    else:
        await channel.send("ℹ️ Немає нових важливих повідомлень на цей момент.")

# Команда !digest для ручного збору
@bot.command()
async def digest(ctx):
    await send_summary(ctx.channel)

# Автоматичний дайджест о 6:00 ранку за Києвом
@tasks.loop(time=datetime.time(hour=6, minute=0, tzinfo=pytz.timezone('Europe/Kyiv')))
async def daily_summary():
    channel = bot.get_channel(CHANNEL_ID)
    await send_summary(channel)

# Запуск бота
bot.run(TOKEN)
