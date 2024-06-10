import os
import ssl
import certifi
import discord
from discord.ext import commands, tasks
import sqlite3
from datetime import datetime, timedelta
import asyncio
import aiohttp
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
ssl_context = ssl.create_default_context(cafile=certifi.where())
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Connect to SQLite database
conn = sqlite3.connect('out_of_town.db')
c = conn.cursor()

# Create a table if it doesn't exist
c.execute('''
CREATE TABLE IF NOT EXISTS out_of_town (
    user_id INTEGER,
    start_date TEXT,
    end_date TEXT
)
''')
conn.commit()

# Define the weekly report task
@tasks.loop(hours=24)  # Check every day to see if it's Sunday
async def weekly_report():
    await bot.wait_until_ready()
    current_date = datetime.now()
    if current_date.weekday() == 6:  # 6 corresponds to Sunday
        next_week = current_date + timedelta(days=7)
        c.execute('SELECT user_id, start_date, end_date FROM out_of_town')
        results = c.fetchall()
        report = ""
       
        report = "People out of town this week :airplane: :\n\n"
        any_out_of_town = False
        
        for user_id, start_date, end_date in results:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            
            if start_date_obj <= next_week and end_date_obj >= current_date:
                user = await bot.fetch_user(user_id)
                report += f":waving_hand: <@{user_id}>: {start_date} to {end_date}\n"
                any_out_of_town = True
        
        if not any_out_of_town:
            report += "No one is out of town for the next 7 days LET'S GO :partying_face: !"

            
        channel = bot.get_channel(1248465122045722685)  # Replace with your channel ID
        await channel.send(report)

# Define the command function for !oot
@bot.command(name='oot', help='Send out of town dates')
async def oot(ctx):
    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    await ctx.send("Please enter your start date (YYYY-MM-DD) :calendar: :")
    try:
        start_msg = await bot.wait_for("message", check=check, timeout=60)
        start_date = start_msg.content
        datetime.strptime(start_date, '%Y-%m-%d')  # Validate date format
    except (asyncio.TimeoutError, ValueError):
        await ctx.send("Invalid date format or timeout. Please try again.")
        return

    await ctx.send("Please enter your end date (YYYY-MM-DD) :calendar: :")
    try:
        end_msg = await bot.wait_for("message", check=check, timeout=60)
        end_date = end_msg.content
        datetime.strptime(end_date, '%Y-%m-%d')  # Validate date format
    except (asyncio.TimeoutError, ValueError):
        await ctx.send("Need to fix how you entered your dates pls")
        return

    user_id = ctx.author.id
    c.execute("INSERT INTO out_of_town VALUES (?, ?, ?)", (user_id, start_date, end_date))
    conn.commit()
    await ctx.send("Your OOT time has been logged. Safe Travels!")

# Start the bot
@bot.event
async def on_ready():
    print('Bot is ready.')
    weekly_report.start()

# Error handling to see if the command is being processed
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send(f'Error: {str(error)}')
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send('Command not found.')
    else:
        await ctx.send(f'An error occurred: {str(error)}')

# Run the bot
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
