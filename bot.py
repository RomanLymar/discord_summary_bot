import discord
from discord.ext import tasks
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

# Інтенти
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# Список важливих повідомлень
important_messages = []

# Часова зона Києва
kyiv_timezone = pytz.timezone('Europe/Kyiv')

# Подія запуску
@bot.event
async def on_ready():
    print(f"✅ Бот запущений як {bot.user}")
    await tree.sync(guild=discord.Object(id=GUILD_ID))  # Синхронізація слеш-команд
    daily_summary.start()

# Обробка повідомлень
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith('!digest'):
        return  # Ігнорувати стару команду !digest у повідомленнях

    guild = bot.get_guild(GUILD_ID)
    member = guild.get_member(message.author.id)

    if member:
        role_names = [role.name for role in member.roles]
        if IMPORTANT_ROLE in role_names:
            important_messages.append(message)

# Слеш-команда /digest
@tree.command(name="digest", description="Зібрати дайджест важливих повідомлень за останні 24 години", guild=discord.Object(id=GUILD_ID))
async def digest_command(interaction: discord.Interaction):
    await send_digest(interaction.channel, is_slash_command=True, interaction=interaction)

# Щоденний автоматичний дайджест
@tasks.loop(minutes=1)
async def daily_summary():
    now = datetime.datetime.now(kyiv_timezone)
    if now.hour == 6 and now.minute == 0:  # 06:00 за Києвом
        channel = bot.get_channel(CHANNEL_ID)
        await send_digest(channel)

# Функція для створення дайджесту
async def send_digest(channel, is_slash_command=False, interaction=None):
    if important_messages:
        today = datetime.datetime.now(kyiv_timezone).date()
        yesterday = today - datetime.timedelta(days=1)

        embed = discord.Embed(
            title=f"📚 Выжимка 2TOP SQUAD {yesterday.strftime('%d.%m')}-{today.strftime('%d.%m')}",
            color=discord.Color.blue()
        )

        for msg in important_messages:
            content_preview = msg.content.split('\n')[0][:100]
            if not content_preview:
                content_preview = "Без тексту (лише вкладення)"
            channel_name = msg.channel.name
            embed.add_field(
                name=f"#{channel_name} – {content_preview}",
                value=f"[Перейти до повідомлення]({msg.jump_url})",
                inline=False
            )

        if is_slash_command:
            await interaction.response.send_message(embed=embed)
        else:
            await channel.send(embed=embed)

        important_messages.clear()
    else:
        if is_slash_command:
            await interaction.response.send_message("ℹ️ Немає нових важливих повідомлень на цей момент.")
        else:
            await channel.send("ℹ️ Немає нових важливих повідомлень на цей момент.")

# Запуск бота
bot.run(TOKEN)
