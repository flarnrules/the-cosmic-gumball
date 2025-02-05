import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

import os
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

GUILD_ID = 1286858214767333499  # Replace with your Discord server ID
WELCOME_CHANNEL_ID = 1336547290298581065  # Replace with your #welcome channel ID

intents = discord.Intents.default()
intents.members = True  # Enables member join events
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} is now online and rolling! 🍬")

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="🎉 Welcome to the Cosmic Gumball Machine! 🎉",
            description=(
                "🍬 Pick a gumball, verify your NFT, and start your journey! 🌈\n\n"
                "🟢 **Step 1:** Complete verification in **#verify**\n"
                "🔵 **Step 2:** Verify your NFT in **#verify-nfts**\n"
                "🟠 **Step 3:** Verify your traits in **#verify-traits**\n\n"
                "🚀 Enjoy your stay, and let the gumball madness begin!"
            ),
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url="YOUR_GUMBALL_IMAGE_URL_HERE")  # Add an image if desired
        await channel.send(f"Welcome, {member.mention}! 🍬", embed=embed)

bot.run(TOKEN)
