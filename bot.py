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

    if guild and message.guild and message.guild.id == GUILD_ID:
        member = guild.get_member(message.author.id)

        if member:
            role_names = [role.name for role in member.roles]
            if IMPORTANT_ROLE in role_names:
                important_messages.append(message)

    await bot.process_commands(message)

# Щоденне надсилання дайджеста
@tasks.loop(time=datetime.time(hour=10, minute=0))
async def daily_summary():
    await send_digest(auto=True)

# Команда ручного надсилання дайджеста
@bot.command()
async def digest(ctx):
    await send_digest(auto=False)

# Функція для надсилання дайджеста
async def send_digest(auto=False):
    channel = bot.get_channel(CHANNEL_ID)
    if not important_messages:
        if not auto:
            await channel.send("ℹ️ Немає нових важливих повідомлень на цей момент.")
        return

    title = "📚 Щоденний дайджест важливих повідомлень" if auto else "📚 Дайджест важливих повідомлень (ручний запуск)"
    embed = discord.Embed(title=title, color=discord.Color.blue() if auto else discord.Color.green())

    for msg in important_messages:
        # Перевіряємо чи повідомлення було у гілці
        thread_info = ""
        if isinstance(msg.channel, discord.Thread):
            thread_info = f"(гілка: {msg.channel.name}) "

        content_preview = msg.content.split('\n')[0][:100]
        if not content_preview:
            content_preview = "Без тексту (можливо тільки вкладення)"

        embed.add_field(
            name=f"{thread_info}{content_preview}",
            value=f"[Перейти до повідомлення]({msg.jump_url})",
            inline=False
        )

    await channel.send(embed=embed)
    important_messages.clear()

# Запуск бота
bot.run(TOKEN)

