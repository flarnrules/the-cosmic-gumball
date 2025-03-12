import discord
from discord.ext import commands
from discord.ui import View, Button
import os
from dotenv import load_dotenv
from mint_relay import relay_mint_message, MINT_FEED_CHANNEL_ID, RELAY_CHANNEL_ID
import logging
from PIL import Image, ImageDraw, ImageFont
import os
import random
import json
import asyncio

load_dotenv()

BACKGROUND_DIR = "../frogs/collections/10-cosmic-gumball-machine/frogs_art_engine/media/layers/core_layers/background"


TOKEN = os.getenv("DISCORD_BOT_TOKEN")

GUILD_ID = 1286858214767333499
GENERAL_CHANNEL_ID = 1336212816415424513
WELCOME_CHANNEL_ID = 1336547290298581065
VERIFY_HUMAN_CHANNEL_ID = 1336547466799222814
VERIFIED_ROLE_ID = 1339113346229862460
SHRINE_CHANNEL_ID = 1339853650650206292
SHRINE_FILE = "gumball_shrine.json"


intents = discord.Intents.default()
intents.members = True  # Enables member join events
intents.messages = True  # Needed for message content tracking
intents.message_content = True  # Explicitly enable message content intent
intents.guilds = True
intents.webhooks = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Ensure shrine file exists or create it
if not os.path.exists(SHRINE_FILE):
    logging.warning("⚠️ Shrine JSON file not found. Creating a new one.")
    with open(SHRINE_FILE, "w") as f:
        json.dump({"count": 0}, f)

# Load shrine data
try:
    with open(SHRINE_FILE, "r") as f:
        shrine_data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    logging.error(f"❌ Failed to load shrine data: {e}")
    shrine_data = {"count": 0}  # Default if the file is corrupt



class VerifyButton(View):
    """A button that assigns the Verified Human role when clicked."""
    
    def __init__(self):
        super().__init__(timeout=None)  # No timeout

    @discord.ui.button(label="Verify Me!", style=discord.ButtonStyle.green, custom_id="verify_human")
    async def verify_button(self, interaction: discord.Interaction, button: Button):
        """Assigns the Verified Human role when clicked."""
        
        if interaction.guild is None:
            logging.warning("⚠️ Verification interaction received outside a server. Ignoring.")
            await interaction.response.send_message("❌ This action can only be performed inside a server.", ephemeral=True)
            return

        guild = interaction.guild
        member = interaction.user
        role = guild.get_role(VERIFIED_ROLE_ID)

        if not role:
            await interaction.response.send_message("❌ Verification failed. Role not found.", ephemeral=True)
            logging.error("❌ Verified Human role not found.")
            return

        if role in member.roles:
            await interaction.response.send_message("✅ You are already verified!", ephemeral=True)
        else:
            await member.add_roles(role)
            await interaction.response.send_message("🎉 You are now verified!", ephemeral=True)
            logging.info(f"✅ {member.name} verified as human.")



def generate_welcome_image(username):
    """Generates a welcome image with a random background."""
    try:
        # ✅ Get a random background image
        background_files = [f for f in os.listdir(BACKGROUND_DIR) if f.endswith((".png", ".jpg", ".jpeg"))]
        if not background_files:
            logging.error("❌ No background images found in the directory!")
            return None

        random_background = random.choice(background_files)
        background_path = os.path.join(BACKGROUND_DIR, random_background)

        logging.info(f"🎨 Selected background: {random_background}")

        # ✅ Load the background image
        background = Image.open(background_path).convert("RGBA")

        # ✅ Define text overlay
        draw = ImageDraw.Draw(background)
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # Change this if you have a custom font
        font = ImageFont.truetype(font_path, 90)

        text = f"Welcome,\n{username}!"
        text_position = (100, 100)  # Adjust placement
        text_color = (random.randint(1, 255), random.randint(1, 255), random.randint(1, 255))
        outline_color = (random.randint(1, 255), random.randint(1, 255), random.randint(1, 255))

        offsets = [-3, -2, -1, 1, 2, 3]

        # ✅ Draw outline first (multiple times for effect)
        for x_offset in offsets:
            for y_offset in offsets:
                outline_position = (text_position[0] + x_offset, text_position[1] + y_offset)
                draw.text(outline_position, text, font=font, fill=outline_color)

        # ✅ Draw main text on top
        draw.text(text_position, text, font=font, fill=text_color)

        # ✅ Save image to a temp file
        output_path = f"welcome_{username}.png"
        background.save(output_path)
        return output_path

    except Exception as e:
        logging.error(f"❌ Error generating welcome image: {e}")
        return None





@bot.command(name="lastmint")
async def last_mint(ctx):
    """Fetches the most recent mint embed from the Mint Feed channel and relays it."""
    mint_channel = bot.get_channel(MINT_FEED_CHANNEL_ID)  # Get the mint feed channel

    if not mint_channel:
        await ctx.send("❌ I can't find the mint feed channel.")
        logging.error("❌ Mint feed channel not found.")
        return

    try:
        # Fetch the most recent message
        last_message = await anext(mint_channel.history(limit=1), None)
    except Exception as e:
        logging.error(f"❌ Error fetching last message: {e}")
        await ctx.send("❌ Failed to fetch the most recent mint message.")
        return

    if not last_message:
        await ctx.send("❌ No recent mint messages found.")
        logging.warning("❌ No recent messages in mint feed channel.")
        return

    # 🔹 Log full message details
    logging.info(f"📝 Last message fetched: {last_message}")
    logging.info(f"📝 Author: {last_message.author}")
    logging.info(f"📝 Embeds: {last_message.embeds}")

    relay_channel = bot.get_channel(RELAY_CHANNEL_ID)  # Get the relay channel

    if relay_channel:
        # Check if the message contains an embed
        if last_message.embeds:
            embed = last_message.embeds[0]  # Get the first embed
            logging.info(f"✅ Relaying embed: {embed.to_dict()}")  # Log embed data
            await relay_channel.send(embed=embed)
            await ctx.send("✅ Last mint embed has been relayed!")
        else:
            await ctx.send("❌ The last mint message did not contain an embed.")
            logging.warning("❌ Last message had no embed, nothing to relay.")
    else:
        await ctx.send("❌ I can't find the relay channel.")
        logging.error("❌ Relay channel not found.")




@bot.command(name="status")
async def status(ctx):
    """Replies with a list of servers and channels the bot is monitoring."""
    guilds = bot.guilds  # Get all servers the bot is in

    status_message = "🟢 **The Cosmic Gumball is Live!**\n\n"
    status_message += "**Connected Servers & Channels:**\n"

    for guild in guilds:
        status_message += f"🔹 **{guild.name}** (ID: {guild.id})\n"

        for channel in guild.text_channels:
            if channel.id in [MINT_FEED_CHANNEL_ID, RELAY_CHANNEL_ID]:  # Check monitored channels
                status_message += f"   📌 Monitoring: {channel.name} (ID: {channel.id})\n"

    await ctx.send(status_message)

@bot.command(name="testwelcome")
async def test_welcome(ctx):
    """Simulates a new user joining for testing."""
    fake_user = ctx.author  # Use the command sender as the test "new user"
    logging.info(f"🛠️ Simulating welcome for {fake_user.name}")
    await on_member_join(fake_user)

@bot.event
async def on_ready():
    print(f"{bot.user} is now online and rolling! 🍬")

@bot.event
async def on_member_join(member):
    
    """Logs a new member joining and announces in the general chat."""
    general_channel = bot.get_channel(GENERAL_CHANNEL_ID)
    if not general_channel:
        logging.error("❌ General channel not found.")
        return

    # Log the join event
    with open("joins_leaves.log", "a") as log_file:
        log_file.write(f"🟢 {member.name} ({member.id}) joined the server.\n")

    # Send a simple message in general chat
    await general_channel.send(f"🍬 {member.mention} just joined the Cosmic Gumball Machine!")
    
    """Sends a custom welcome message with a random background image."""
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if not channel:
        logging.error("❌ Welcome channel not found.")
        return

    logging.info(f"👤 New member joined: {member.name}")

    # ✅ Generate the welcome image
    image_path = generate_welcome_image(member.name)
    if image_path:
        file = discord.File(image_path, filename="welcome.png")

        # ✅ Define channel links
        verify_human_channel = bot.get_channel(1336547466799222814)  # Replace with actual channel ID
        verify_gumball_channel = bot.get_channel(1336547518288498698)  # Replace with actual ID
        verify_traits_channel = bot.get_channel(1336547704037314631)  # Replace with actual ID

        verify_human_link = f"<#{verify_human_channel.id}>" if verify_human_channel else "⚠️ Channel Not Found"
        verify_gumball_link = f"<#{verify_gumball_channel.id}>" if verify_gumball_channel else "⚠️ Channel Not Found"
        verify_traits_link = f"<#{verify_traits_channel.id}>" if verify_traits_channel else "⚠️ Channel Not Found"

        # ✅ Embed with verification steps
        embed = discord.Embed(
            title=f"🎉 Welcome to the Cosmic Gumball Machine, {member.name}! 🍬",
            description=(
                "Verify you are a human, verify your gumballs, and discover if you have any rare traits!\n\n"
                f"🔹 **Verify human:** {verify_human_link}\n"
                f"🔹 **Verify gumballs:** {verify_gumball_link}\n"
                f"🔹 **Rare traits:** {verify_traits_link}"
            ),
            color=discord.Color.gold()
        )
        embed.set_image(url="attachment://welcome.png")

        await channel.send(f"Welcome, {member.mention}! 🍬", file=file, embed=embed)

        # ✅ Cleanup temp image file
        os.remove(image_path)
    else:
        await channel.send(f"Welcome, {member.mention}! 🍬 (Image failed to generate)")

@bot.event
async def on_message(message):
    # ✅ Ignore messages that aren't from a server (DMs, webhooks, etc.)
    if message.guild is None:
        logging.warning("⚠️ Received a message outside of a server. Ignoring.")
        return

    # ✅ Allow webhook messages, but ignore all other bot messages
    if message.author.bot and message.webhook_id is None:
        return

    logging.info(f"📩 Message received in {message.guild.name}, channel: {message.channel.name} ({message.channel.id}): {message.content}")

    # ✅ Detect Webhook Messages in Mint Feed Channel
    if message.channel.id == MINT_FEED_CHANNEL_ID:
        logging.info(f"🔍 Detected a message in the Mint Feed Channel from {message.author.name} (Webhook: {message.webhook_id is not None})")
        logging.info(f"📝 Message Type: {message.type}")
        logging.info(f"📝 Embeds: {message.embeds}")
        logging.info(f"📝 Attachments: {message.attachments}")

        relay_channel = bot.get_channel(RELAY_CHANNEL_ID)

        if relay_channel:
            if message.embeds:
                embed = message.embeds[0]  # Get the first embed
                logging.info(f"✅ Instantly relaying mint embed from webhook: {embed.to_dict()}")
                await relay_channel.send(embed=embed)
            else:
                logging.warning("❌ Webhook message had no embed, skipping relay.")
        else:
            logging.error("❌ Relay channel not found.")

    # ✅ Process bot commands first
    if message.content.startswith("!"):
        logging.info(f"✅ Processing command: {message.content}")
        await bot.process_commands(message)
        return  # Exit early, don’t check for relays

    # ✅ Gumball Alert System with Streak Tracking
    if "gumball" in message.content.lower():  # Check for "gumball" (case-insensitive)
        general_channel = bot.get_channel(GENERAL_CHANNEL_ID)

        # ✅ First-time alert message (kept from original)
        if general_channel:
            await general_channel.send(
                f"🍬 **Gumball Alert!** {message.author.mention} just said gumball! 🟣🔵🟢"
            )

        # Ensure user streaks are tracked
        if not hasattr(bot, "gumball_streaks"):
            bot.gumball_streaks = {}

        author_id = message.author.id

        if author_id not in bot.gumball_streaks:
            bot.gumball_streaks[author_id] = {"count": 0, "last_message_time": None}

        # Reset streak if more than 10 minutes have passed
        last_time = bot.gumball_streaks[author_id]["last_message_time"]
        if last_time and (message.created_at - last_time).total_seconds() > 600:
            bot.gumball_streaks[author_id]["count"] = 0

        # Increase count and update last message time
        bot.gumball_streaks[author_id]["count"] += 1
        bot.gumball_streaks[author_id]["last_message_time"] = message.created_at
        streak_count = bot.gumball_streaks[author_id]["count"]

        # Response based on streak count
        if streak_count == 2:
            await general_channel.send(
                f"🟢🔵🟣 **Gumball Alert Update!** {message.author.mention} has said gumball again! "
                f"The gumball energy is rising... 🍬"
            )
        elif streak_count == 3:
            await general_channel.send(
                f"🟢🔵🟣 **GUMBALL ALERT INTENSIFYING!** {message.author.mention} has now said gumball **3 times in a row!** "
                f"The system is detecting a surge in gumball frequency! 🍬🟢🔵"
            )
        elif streak_count == 4:
            await general_channel.send(
                f"🔴🟠🟡 **🚨 GUMBALL ALERT LEVEL 4 🚨** {message.author.mention} is approaching critical gumball mass! "
                f"Prepare for possible containment breach! 🍬🟢🔵🟣🔴"
            )
        elif streak_count == 5:
            await general_channel.send(
                f"🔴🟠🟡 **🚨🚨 MAXIMUM GUMBALL ALERT 🚨🚨** {message.author.mention} has reached **5 consecutive gumball mentions!** "
                f"**The Gumball System is at full capacity! MULTICOLORED GUMBALLS ARE EVERYWHERE!** 🟢🔵🟣🔴🟠🟡🍬"
            )

            # Assign "ON FIRE 🔥" role
            fire_role = discord.utils.get(message.guild.roles, name="ON FIRE 🔥")
            if fire_role:
                await message.author.add_roles(fire_role)
                logging.info(f"🔥 {message.author.name} has been given the ON FIRE 🔥 role.")

                # Remove role after 1 hour
                async def remove_fire_role():
                    await asyncio.sleep(3600)  # 1 hour
                    if fire_role in message.author.roles:
                        await message.author.remove_roles(fire_role)
                        logging.info(f"🔥 {message.author.name} no longer ON FIRE.")

                bot.loop.create_task(remove_fire_role())

    await bot.process_commands(message)  # Ensure other commands still work


@bot.command(name="checklast")
async def check_last_message(ctx):
    """Checks details about the latest message in the Mint Feed channel."""
    mint_channel = bot.get_channel(MINT_FEED_CHANNEL_ID)

    if not mint_channel:
        await ctx.send("❌ I can't find the mint feed channel.")
        return

    last_message = await anext(mint_channel.history(limit=1), None)

    if not last_message:
        await ctx.send("❌ No recent messages found.")
        return

    logging.info(f"📝 Last message fetched: {last_message}")
    logging.info(f"📝 Author: {last_message.author} (Bot: {last_message.author.bot})")
    logging.info(f"📝 Is Webhook: {last_message.webhook_id is not None}")
    logging.info(f"📝 Message Type: {last_message.type}")
    logging.info(f"📝 Embeds: {last_message.embeds}")

    response = (
        f"**Last Message Details:**\n"
        f"👤 Author: {last_message.author} (Bot: {last_message.author.bot})\n"
        f"🕸️ Webhook Message: {'Yes' if last_message.webhook_id else 'No'}\n"
        f"📌 Message Type: {last_message.type}\n"
        f"📦 Contains Embeds: {'Yes' if last_message.embeds else 'No'}"
    )

    await ctx.send(response)

@bot.command(name="setupverify")
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    """Posts the verification button in the verify-human channel."""
    channel = bot.get_channel(VERIFY_HUMAN_CHANNEL_ID)
    if not channel:
        logging.error("❌ Verify-human channel not found.")
        return

    embed = discord.Embed(
        title="🔹 Human Verification Required",
        description="Click the button below to verify you are human and gain access to the server.",
        color=discord.Color.blue(),
    )

    await channel.send(embed=embed, view=VerifyButton())
    await ctx.send("✅ Verification message posted!")

@bot.event
async def on_member_remove(member):
    """Logs a member leaving, announces in general, and enshrines them in the Gumball Shrine."""
    general_channel = bot.get_channel(GENERAL_CHANNEL_ID)
    shrine_channel = bot.get_channel(SHRINE_CHANNEL_ID)

    if not general_channel:
        logging.error("❌ General channel not found.")
        return
    if not shrine_channel:
        logging.error("❌ Shrine channel not found. Check SHRINE_CHANNEL_ID.")
        return

    # Increment shrine counter
    shrine_data["count"] += 1
    gumball_number = shrine_data["count"]

    logging.info(f"🔢 Gumball count incremented: {gumball_number}")

    # Save updated shrine count
    try:
        with open(SHRINE_FILE, "w") as f:
            json.dump(shrine_data, f)
        logging.info(f"✅ Shrine data updated: {shrine_data}")
    except Exception as e:
        logging.error(f"❌ Failed to save shrine data: {e}")

    # Log the leave event
    with open("joins_leaves.log", "a") as log_file:
        log_file.write(f"🔴 {member.name} ({member.id}) left the server. Gumball #{gumball_number} added to the shrine.\n")

    # Send a simple message in general chat
    await general_channel.send(f"🍬 {member.name} has transcended the Cosmic Gumball Machine... Gumball #{gumball_number} now drifts through the cosmos.")

    # Enshrine them in the shrine channel
    shrine_message = (
        f"🌌 **Gumball #{gumball_number}: {member.name}** 🌌\n"
        f"They have left the Cosmic Gumball Machine and are now enshrined as a luminous gumball, forever floating in the fabric of the cosmos. 🛸✨"
    )

    try:
        await shrine_channel.send(shrine_message)
        logging.info(f"✅ Successfully enshrined Gumball #{gumball_number} ({member.name}) in the shrine.")
    except Exception as e:
        logging.error(f"❌ Failed to send shrine message: {e}")


bot.run(TOKEN)
