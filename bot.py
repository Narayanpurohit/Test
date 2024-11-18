import os
import time
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient

# Replace with your actual bot token and credentials
API_ID = "15191874"
API_HASH = "3037d39233c6fad9b80d83bb8a339a07"
TOKEN = "7481801715:AAEV22RePMaDqd2tyxH0clxtnqd5hDpRuTw"

# Initialize the Pyrogram Client
app = Client("watermark_bot", bot_token=TOKEN, api_id=API_ID, api_hash=API_HASH)

# Connect to MongoDB
client = MongoClient("mongodb+srv://1by1themes:3snVjsLPmZ9xcbd3@cluster0.uaazt.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["watermark_bot_db"]
users_collection = db["users"]

# Default settings
DEFAULT_WATERMARK_TEXT = "My Watermark"
DEFAULT_POSITION = "bottom-right"
DEFAULT_SIZE = "medium"  # Options: small, medium, large

FONT_SIZES = {
    "small": 0.5,
    "medium": 1,
    "large": 2
}

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

# Function to get user settings
def get_user_settings(user_id):
    user_data = users_collection.find_one({"user_id": user_id})
    if user_data:
        return user_data
    return None

# Function to add a new user to the database
def add_new_user(user_id):
    default_data = {
        "user_id": user_id,
        "watermark_text": DEFAULT_WATERMARK_TEXT,
        "position": DEFAULT_POSITION,
        "size": DEFAULT_SIZE,
    }
    users_collection.insert_one(default_data)
    logger.info(f"New user added to database: {user_id}")
    return default_data

# Function to update user settings
def update_user_settings(user_id, settings):
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": settings},
        upsert=True
    )
    logger.info(f"Updated settings for {user_id}: {settings}")

# Function to add a watermark to a video
def add_watermark(video_path, output_path, text, position, size):
    # Example implementation
    from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

    video = VideoFileClip(video_path)
    font_size = {"small": 30, "medium": 50, "large": 70}.get(size, 50)
    watermark = TextClip(text, fontsize=font_size, color='white')

    if position == "top-left":
        watermark = watermark.set_position(("left", "top"))
    elif position == "top-right":
        watermark = watermark.set_position(("right", "top"))
    elif position == "bottom-left":
        watermark = watermark.set_position(("left", "bottom"))
    elif position == "bottom-right":
        watermark = watermark.set_position(("right", "bottom"))
    else:
        watermark = watermark.set_position(("center", "center"))

    final_video = CompositeVideoClip([video, watermark])
    final_video.write_videofile(output_path, codec="libx264", fps=24)

# Start command
@app.on_message(filters.command("start"))
async def start(client, message: Message):
    user_id = message.from_user.id
    user_data = get_user_settings(user_id)

    if not user_data:
        user_data = add_new_user(user_id)

    await message.reply_text(
        f"👋 Welcome to the Watermark Bot!\n\n"
        f"Your default settings:\n"
        f"Watermark Text: `{user_data['watermark_text']}`\n"
        f"Position: `{user_data['position']}`\n"
        f"Size: `{user_data['size']}`\n\n"
        "Send me a video to add a watermark, or use /help for commands."
    )

# Help command
@app.on_message(filters.command("help"))
async def help(client, message: Message):
    await message.reply_text(
        "📜 HELP MENU 📜\n\n"
        "Use the following commands:\n"
        "/set_watermark <text> - Set the watermark text.\n"
        "/position <top-left|top-right|bottom-left|bottom-right> - Set the position.\n"
        "/size <small|medium|large> - Set watermark size."
    )

# Set watermark text
@app.on_message(filters.command("set_watermark"))
async def set_watermark(client, message: Message):
    if len(message.text.split()) < 2:
        await message.reply_text("⚠️ Please provide the watermark text (e.g., `/set_watermark MyText`).")
        return
    text = " ".join(message.text.split()[1:])
    update_user_settings(message.from_user.id, {"watermark_text": text})
    await message.reply_text(f"✅ Watermark text updated to: `{text}`")

# Set position
@app.on_message(filters.command("position"))
async def set_position(client, message: Message):
    if len(message.text.split()) < 2:
        await message.reply_text("⚠️ Please provide the position (e.g., `/position top-right`).")
        return
    position = message.text.split()[1]
    if position not in ["top-left", "top-right", "bottom-left", "bottom-right"]:
        await message.reply_text("⚠️ Invalid position. Use top-left, top-right, bottom-left, or bottom-right.")
        return
    update_user_settings(message.from_user.id, {"position": position})
    await message.reply_text(f"✅ Position updated to: `{position}`")

# Set size
@app.on_message(filters.command("size"))
async def set_size(client, message: Message):
    if len(message.text.split()) < 2:
        await message.reply_text("⚠️ Please provide the size (e.g., `/size medium`).")
        return
    size = message.text.split()[1]
    if size not in FONT_SIZES:
        await message.reply_text("⚠️ Invalid size. Use small, medium, or large.")
        return
    update_user_settings(message.from_user.id, {"size": size})
    await message.reply_text(f"✅ Size updated to: `{size}`")

# Handle video uploads
@app.on_message(filters.video | filters.document)
async def handle_video(client, message: Message):
    user_id = message.from_user.id
    user_data = get_user_settings(user_id) or add_new_user(user_id)

    watermark_text = user_data["watermark_text"]
    position = user_data["position"]
    size = user_data["size"]

    progress_message = await message.reply_text("📥 Downloading your video...")

    try:
        video_path = await message.download()
        output_path = f"{video_path}.watermarked.mp4"

        add_watermark(video_path, output_path, watermark_text, position, size)

        await progress_message.edit_text("📤 Uploading your watermarked video...")
        await message.reply_video(output_path, supports_streaming=True)

        os.remove(video_path)
        os.remove(output_path)
        await progress_message.edit_text("✅ Video processed successfully!")

    except Exception as e:
        await progress_message.edit_text("❌ An error occurred during processing.")
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    app.run()