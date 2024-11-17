import os
import cv2
import time
import subprocess
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InputMediaPhoto
from pymongo import MongoClient
from pyrogram.errors import FloodWait

# Replace with your actual bot token and credentials
API_ID = "15191874"  # Get this from my.telegram.org
API_HASH = "3037d39233c6fad9b80d83bb8a339a07"  # Get this from my.telegram.org
TOKEN = "7481801715:AAEV22RePMaDqd2tyxH0clxtnqd5hDpRuTw"  # Replace with your bot's token

# Initialize the Pyrogram Client
app = Client("watermark_bot", bot_token=TOKEN, api_id=API_ID, api_hash=API_HASH)

# Connect to MongoDB (replace with your MongoDB URI if using a hosted service like Atlas)
client = MongoClient("mongodb://localhost:27017/")
db = client["watermark_bot_db"]
users_collection = db["users"]

# Default settings
DEFAULT_TEXT = "jn-bots.in"
DEFAULT_POSITION = "bottom-right"
DEFAULT_SNAPSHOTS = 8
DEFAULT_FONT = "𝒜𝐵𝒞𝒟𝐸𝐹𝒢𝐻𝐼𝒥𝒦𝒻"
DEFAULT_SIZE = "medium"  # Options: small, medium, large

# Define sizes based on small, medium, large
FONT_SIZES = {
    "small": 0.5,
    "medium": 1,
    "large": 2
}

# List of available fonts (add more if needed)
FONTS = {
    "𝒜𝐵𝒞𝒟𝐸𝐹𝒢𝐻𝐼𝒥𝒦𝒻": "Font1",
    "𝔸𝔹ℂ𝔻𝔼ℱℂℍ𝕀𝕁K": "Font2",
}

# Set up logging to log each function execution
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

# Function to get user settings from MongoDB (if exists)
def get_user_settings(user_id):
    user_data = users_collection.find_one({"user_id": user_id})
    if user_data:
        logger.info(f"Retrieved user settings for {user_id}")
        return user_data
    logger.info(f"No settings found for {user_id}, using defaults.")
    return {}

# Function to update user settings in MongoDB
def update_user_settings(user_id, settings):
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": settings},
        upsert=True
    )
    logger.info(f"Updated settings for {user_id}: {settings}")

# Function to add a watermark to a video (without audio)
def add_watermark(video_path, output_path, text=DEFAULT_TEXT, position=None, font=DEFAULT_FONT,
                  size=DEFAULT_SIZE, movement="moving", speed=2, direction="horizontal", loop=True, progress_callback=None):
    logger.info(f"Starting watermarking process for video: {video_path} with watermark text: {text}")
    video = cv2.VideoCapture(video_path)
    fps = video.get(cv2.CAP_PROP_FPS)
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

    # OpenCV VideoWriter for processing frames without audio
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    temp_video_path = "temp_video_no_audio.mp4"
    out = cv2.VideoWriter(temp_video_path, fourcc, fps, (width, height))

    font_scale = FONT_SIZES.get(size, 1)
    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)[0]

    # Set initial position for moving watermark
    if movement == "moving":
        x, y = 0, height // 2  # Start from the left middle
        dx, dy = (speed, 0) if direction == "horizontal" else (0, speed)
    else:
        x, y = {
            "top-left": (10, 30),
            "top-right": (width - text_size[0] - 10, 30),
            "bottom-left": (10, height - 20),
            "bottom-right": (width - text_size[0] - 10, height - 20),
            "center": ((width - text_size[0]) // 2, height // 2)
        }.get(position, (10, 30))  # Default to top-left if no position specified
    
    frame_count = 0
    last_update_time = time.time()

    while True:
        ret, frame = video.read()
        if not ret:
            break

        # Update watermark position for movement if applicable
        if movement == "moving":
            x = (x + dx) % (width - text_size[0]) if loop else min(x + dx, width - text_size[0])

        # Add watermark with red outline
        cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), 1, cv2.LINE_AA)
        out.write(frame)
        frame_count += 1

        # Update progress at intervals
        if progress_callback and time.time() - last_update_time > 1:
            progress_callback(frame_count, total_frames)
            last_update_time = time.time()

    video.release()
    out.release()

    # Combine the processed video with original audio using ffmpeg
    command = [
        "ffmpeg", "-y", "-i", temp_video_path, "-i", video_path, "-c:v", "copy", "-c:a", "aac",
        "-map", "0:v:0", "-map", "1:a:0", output_path
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Clean up temporary file
    os.remove(temp_video_path)
    logger.info(f"Watermarking process completed. Output saved to {output_path}")

# Function to capture snapshots
def capture_snapshots(video_path, snapshot_count=DEFAULT_SNAPSHOTS):
    logger.info(f"Capturing {snapshot_count} snapshots from video: {video_path}")
    snapshots = []
    video = cv2.VideoCapture(video_path)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    step = total_frames // snapshot_count

    for i in range(snapshot_count):
        video.set(cv2.CAP_PROP_POS_FRAMES, i * step)
        ret, frame = video.read()
        if ret:
            snapshot_path = f"snapshot_{i}.jpg"
            cv2.imwrite(snapshot_path, frame)
            snapshots.append(snapshot_path)

    video.release()
    logger.info(f"Captured {len(snapshots)} snapshots")
    return snapshots

# Function to display download progress bar
def progress_bar(current, total, prefix='', length=40):
    percent = ("{0:.1f}").format(100 * (current / float(total)))
    filled_length = int(length * current // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% Complete', end="\r")
    if current == total:
        print()  # New line when complete

# Command to start the bot
@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text(
        "👋 WELCOME to the Watermark Bot!\n\n"
        "Send me a video, and I'll add a watermark to it. You can also configure settings for snapshots, "
        "watermark movement, font style, and size.\n\n"
        "Use /help to see all available commands."
    )
    logger.info(f"User {message.from_user.id} started the bot.")

# Command to display help
@app.on_message(filters.command("help"))
async def help(client, message: Message):
    await message.reply_text(
        "📜 HELP MENU 📜\n\n"
        "Use the following commands to control the bot:\n"
        "/set_watermark <text> - Set the watermark text.\n"
        "/font <font_name> - Set the watermark font (e.g., Font1, Font2).\n"
        "/size <small|medium|large> - Set watermark font size.\n"
        "/snapshots <number> - Set number of snapshots to capture.\n"
        "/start - Start using the bot.\n"
    )
    logger.info(f"User {message.from_user.id} requested help.")

# Command to set watermark text
@app.on_message(filters.command("set_watermark"))
async def set_watermark(client, message: Message):
    if len(message.text.split()) < 2:
        await message.reply_text("⚠️ Please provide the watermark text (e.g., `/set_watermark MyText`).")
        return
    watermark_text = " ".join(message.text.split()[1:])
    user_id = message.from_user.id
    update_user_settings(user_id, {"watermark_text": watermark_text})
    await message.reply_text(f"✅ Watermark text has been set to: {watermark_text}")

# Command to set watermark font
@app.on_message(filters.command("font"))
async def set_font(client, message: Message):
    if len(message.text.split()) < 2:
        await message.reply_text("⚠️ Please provide the font name (e.g., `/font Font1`).")
        return
    font_name = message.text.split()[1]
    if font_name not in FONTS:
        await message.reply_text(f"⚠️ Invalid font. Available options are: {', '.join(FONTS.keys())}")
        return
    user_id = message.from_user.id
    update_user_settings(user_id, {"font": font_name})
    await message.reply_text(f"✅ Font has been set to: {font_name}")

# Command to set watermark size
@app.on_message(filters.command("size"))
async def set_size(client, message: Message):
    if len(message.text.split()) < 2:
        await message.reply_text("⚠️ Please provide the size (e.g., `/size medium`).")
        return
    size = message.text.split()[1]
    if size not in FONT_SIZES:
        await message.reply_text(f"⚠️ Invalid size. Available options are: {', '.join(FONT_SIZES.keys())}")
        return
    user_id = message.from_user.id
    update_user_settings(user_id, {"size": size})
    await message.reply_text(f"✅ Size has been set to: {size}")

# Main method to run the bot
if __name__ == "__main__":
    app.run()