import discord
from discord.ext import commands
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Mint feed relay channel IDs
MINT_FEED_CHANNEL_ID = 1335990324039909529  # Mint feed server
RELAY_CHANNEL_ID = 1336212729849188395  # Cosmic Gumball server

async def relay_mint_message(message, bot):
    """Relays messages from the mint feed server to the Cosmic Gumball server."""
    
    # Log every message the bot sees
    logging.info(f"🔍 Checking message from server: {message.guild.name}, channel: {message.channel.name} ({message.channel.id}): {message.content}")

    if message.channel.id == MINT_FEED_CHANNEL_ID:
        relay_channel = bot.get_channel(RELAY_CHANNEL_ID)
        if relay_channel:
            logging.info(f"✅ Relaying message to {relay_channel.guild.name} ({relay_channel.name}): {message.content}")
            await relay_channel.send(f"🟣 **New Mint!** {message.content}")
        else:
            logging.error(f"❌ Could not find relay channel {RELAY_CHANNEL_ID}")
    else:
        logging.info(f"❌ Ignoring message from unrelated channel ({message.channel.id})")