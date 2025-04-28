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
    member = guild.get_member(message.author.id)

    if member:
        role_names = [role.name for role in member.roles]
        if IMPORTANT_ROLE in role_names:
            important_messages.append(message)

    await bot.process_commands(message)

# Щоденне надсилання дайджеста
@tasks.loop(time=datetime.time(hour=10, minute=0))
async def daily_summary():
    await send_digest()

# Функція для надсилання дайджеста
async def send_digest(manual=False, ctx=None):
    channel = bot.get_channel(CHANNEL_ID)
    if important_messages:
        today = datetime.datetime.utcnow().date()
        yesterday = today - datetime.timedelta(days=1)

        title = f"Выжимка 2TOP SQUAD {yesterday.strftime('%d.%m')}-{today.strftime('%d.%m')}"
        color = discord.Color.green() if manual else discord.Color.blue()

        embed = discord.Embed(
            title=title,
            color=color
        )

        for msg in important_messages:
            content_preview = msg.content.split('\n')[0][:100]
            if not content_preview:
                content_preview = "Без тексту (можливо тільки вкладення)"

            # Видалити слово "digest" або "!digest" на початку
            if content_preview.lower().startswith('!digest') or content_preview.lower().startswith('digest'):
                parts = content_preview.split(' ', 1)
                content_preview = parts[1] if len(parts) > 1 else ''

            embed.add_field(
                name=f"#{msg.channel.name} – {content_preview}",
                value=f"[Перейти до повідомлення]({msg.jump_url})",
                inline=False
            )

        if ctx:
            await ctx.send(embed=embed)
        else:
            await channel.send(embed=embed)

        important_messages.clear()
    else:
        if ctx:
            await ctx.send("ℹ️ Немає нових важливих повідомлень на цей момент.")

# Ручна команда для надсилання дайджеста
@bot.command()
async def digest(ctx):
    await send_digest(manual=True, ctx=ctx)

# Запуск бота
bot.run(TOKEN)
