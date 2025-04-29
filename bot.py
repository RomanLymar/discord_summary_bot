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

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Бот запущений як {bot.user}")
    daily_summary.start()

# Збір важливих повідомлень за попередній день
async def collect_important_messages():
    guild = bot.get_guild(GUILD_ID)
    summary_mention = f"<@&{SUMMARY_ROLE_ID}>"

    now = datetime.datetime.now(pytz.timezone('Europe/Kyiv'))
    start = (now - datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + datetime.timedelta(days=1)

    messages = []

    for channel in guild.text_channels:
        try:
            async for msg in channel.history(after=start, before=end, oldest_first=True):
                if summary_mention in msg.content and not msg.author.bot:
                    messages.append(msg)
        except (discord.Forbidden, discord.HTTPException):
            continue

    return messages

# Надсилання дайджесту
async def send_summary(channel):
    important_messages = await collect_important_messages()

    if important_messages:
        now = datetime.datetime.now(pytz.timezone('Europe/Kyiv'))
        summary_date = (now - datetime.timedelta(days=1)).strftime('%d.%m')

        embed = discord.Embed(
            title=f"📚 Выжимка 2TOP SQUAD {summary_date}",
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
    else:
        await channel.send("ℹ️ Немає нових важливих повідомлень на цей момент.")

# Ручна команда !digest
@bot.command()
async def digest(ctx):
    await send_summary(ctx.channel)

# Автоматичний дайджест о 6:00 ранку за Києвом
@tasks.loop(time=datetime.time(hour=6, minute=0, tzinfo=pytz.timezone('Europe/Kyiv')))
async def daily_summary():
    channel = bot.get_channel(CHANNEL_ID)
    await send_summary(channel)

bot.run(TOKEN)


