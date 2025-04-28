import discord
from discord.ext import commands, tasks
from discord import app_commands
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
tree = app_commands.CommandTree(bot)

important_messages = []

# Функція для перевірки, чи повідомлення важливе
def is_important_message(message):
    if message.author.bot:
        return False
    if message.content.startswith("!digest") or message.content.startswith("/digest"):
        return False

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return False

    member = guild.get_member(message.author.id)
    if not member:
        return False

    role_names = [role.name for role in member.roles]
    return IMPORTANT_ROLE in role_names

# Подія при запуску бота
@bot.event
async def on_ready():
    print(f"✅ Бот запущений як {bot.user}")
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    daily_summary.start()

# Обробка нових повідомлень
@bot.event
async def on_message(message):
    if is_important_message(message):
        important_messages.append(message)

    await bot.process_commands(message)

# Функція для створення дайджеста
async def send_digest():
    channel = bot.get_channel(CHANNEL_ID)
    if not important_messages:
        await channel.send("ℹ️ Немає нових важливих повідомлень на цей момент.")
        return

    kyiv_tz = pytz.timezone('Europe/Kyiv')
    today = datetime.datetime.now(kyiv_tz)
    yesterday = today - datetime.timedelta(days=1)
    date_range = f"{yesterday.strftime('%d.%m')}–{today.strftime('%d.%m')}"

    embed = discord.Embed(
        title=f"📚 Выжимка 2TOP SQUAD {date_range}",
        color=discord.Color.blue()
    )

    for msg in important_messages:
        if msg.channel and msg.content:
            content_preview = msg.content.split('\n')[0][:80]
            if not content_preview:
                content_preview = "Без тексту (лише вкладення)"

            embed.add_field(
                name=f"#{msg.channel.name} – {content_preview}",
                value=f"[Перейти до повідомлення]({msg.jump_url})",
                inline=False
            )

    await channel.send(embed=embed)
    important_messages.clear()

# Автоматичне надсилання щодня о 6 ранку
@tasks.loop(time=datetime.time(hour=6, minute=0, tzinfo=pytz.timezone('Europe/Kyiv')))
async def daily_summary():
    await send_digest()

# Slash-команда /digest
@tree.command(name="digest", description="Згенерувати дайджест важливих повідомлень вручну", guild=discord.Object(id=GUILD_ID))
async def digest(interaction: discord.Interaction):
    await interaction.response.defer()
    await send_digest()

# Запуск бота
bot.run(TOKEN)
