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

# Функція для отримання дати в Києві
def get_kyiv_date():
    tz = pytz.timezone('Europe/Kyiv')
    now = datetime.datetime.now(tz)
    yesterday = now - datetime.timedelta(days=1)
    return yesterday.strftime("%d.%m"), now.strftime("%d.%m")

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

    guild = bot.get_guild(GUILD_ID)
    member = guild.get_member(message.author.id)

    if member:
        role_names = [role.name for role in member.roles]
        if IMPORTANT_ROLE in role_names and not message.content.startswith(("!digest", "/digest")):
            important_messages.append(message)

    await bot.process_commands(message)

# Команда !digest
@bot.command()
async def digest(ctx):
    await send_summary(ctx.channel)

# Автоматичний щоденний дайджест о 6 ранку за Києвом
@tasks.loop(minutes=1)
async def daily_summary():
    kyiv_time = datetime.datetime.now(pytz.timezone('Europe/Kyiv'))
    if kyiv_time.hour == 6 and kyiv_time.minute == 0:
        channel = bot.get_channel(CHANNEL_ID)
        await send_summary(channel)

# Функція надсилання дайджесту
async def send_summary(channel):
    if important_messages:
        embed = discord.Embed(
            title=f"Выжимка 2TOP SQUAD {get_kyiv_date()[0]}-{get_kyiv_date()[1]}",
            color=discord.Color.blue()
        )

        for msg in important_messages:
            if msg.content.strip() == "":
                continue  # Пропустити порожні повідомлення

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

# Запуск бота
bot.run(TOKEN)
