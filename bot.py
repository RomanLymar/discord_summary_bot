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
    channel = bot.get_channel(CHANNEL_ID)
    if important_messages:
        embed = discord.Embed(
            title="📚 Щоденний дайджест важливих повідомлень",
            color=discord.Color.blue()
        )

        for msg in important_messages:
            content_preview = msg.content.split('\n')[0][:100]
            if not content_preview:
                content_preview = "Без тексту (можливо тільки вкладення)"

            embed.add_field(
                name=content_preview,
                value=f"[Перейти до повідомлення]({msg.jump_url})",
                inline=False
            )

        await channel.send(embed=embed)
        important_messages.clear()

# Ручна команда для надсилання дайджеста
@bot.command()
async def digest(ctx):
    if important_messages:
        embed = discord.Embed(
            title="📚 Дайджест важливих повідомлень (ручний запуск)",
            color=discord.Color.green()
        )

        for msg in important_messages:
            content_preview = msg.content.split('\n')[0][:100]
            if not content_preview:
                content_preview = "Без тексту (можливо тільки вкладення)"

            embed.add_field(
                name=content_preview,
                value=f"[Перейти до повідомлення]({msg.jump_url})",
                inline=False
            )

        await ctx.send(embed=embed)
    else:
        await ctx.send("ℹ️ Немає нових важливих повідомлень на цей момент.")

# Запуск бота
bot.run(TOKEN)

