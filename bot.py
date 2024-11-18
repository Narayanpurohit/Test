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
client = MongoClient("mongodb+srv://1by1themes:3snVjsLPmZ9xcbd3@cluster0.uaazt.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
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

def add_watermark(input_path, output_path, text, position, size, snapshots):
    video = VideoFileClip(input_path)

    # Set watermark size
    font_size = {"small": 30, "medium": 50, "large": 70}.get(size, 50)

    # Create TextClip
    watermark = TextClip(text, fontsize=font_size, color='white')
    watermark = watermark.set_duration(video.duration)

    # Set position
    if position == "top-left":
        watermark = watermark.set_position(("left", "top"))
    elif position == "top-right":
        watermark = watermark.set_position(("right", "top"))
    elif position == "bottom-left":
        watermark = watermark.set_position(("left", "bottom"))
    elif position == "bottom-right":
        watermark = watermark.set_position(("right", "bottom"))
    else:  # Default position
        watermark = watermark.set_position(("center", "center"))

    # Merge watermark with video
    final_video = CompositeVideoClip([video, watermark])
    final_video.write_videofile(output_path, codec="libx264", fps=24)

    # Optionally create snapshots
    if snapshots > 0:
        snapshot_interval = video.duration / snapshots
        for i in range(snapshots):
            snapshot_time = snapshot_interval * i
            video.save_frame(f"{output_path}_snapshot_{i + 1}.jpg", t=snapshot_time)

# Handle Video/Document
@app.on_message(filters.video | filters.document)
async def handle_video_or_document(client, message: Message):
    user_id = message.from_user.id
    user_data = users_collection.find_one({"user_id": user_id})

    if not user_data:
        # Default user settings if not in database
        user_data = {
            "watermark_text": "My Watermark",
            "position": "top-right",
            "size": "medium",
            "snapshots": 5
        }
        users_collection.insert_one({"user_id": user_id, **user_data})

    text = user_data.get('watermark_text', "My Watermark")
    position = user_data.get('position', "top-right")
    size = user_data.get('size', "medium")
    snapshots = user_data.get('snapshots', 5)

    progress_message = await message.reply_text("📥 Starting download...")

    start_time = time.time()

    # Progress Callback
    def progress_callback(current, total):
        elapsed_time = time.time() - start_time
        percentage = current / total * 100
        speed = current / elapsed_time if elapsed_time > 0 else 0
        time_left = (total - current) / speed if speed > 0 else 0

        bar = "🟩" * int(percentage // 5) + "⬜️" * (20 - int(percentage // 5))
        formatted_message = (
            f"📥 **Downloading... from DC4**\n\n"
            f"[{bar}] {percentage:.2f}%\n"
            f"➔ {current / 1_048_576:.2f} MB of {total / 1_048_576:.2f} MB\n"
            f"➔ **Speed**: {speed / 1_048_576:.2f} MB/s\n"
            f"➔ **Time Left**: {int(time_left)}s"
        )
        client.loop.create_task(progress_message.edit_text(formatted_message))

    try:
        video_path = await message.download(progress=progress_callback)

        output_path = f"{video_path}.watermarked.mp4"

        add_watermark(
            input_path=video_path,
            output_path=output_path,
            text=text,
            position=position,
            size=size,
            snapshots=snapshots
        )

        await progress_message.edit_text("📤 Uploading your watermarked video...")
        await message.reply_video(output_path, supports_streaming=True)

        # Clean up temporary files
        os.remove(video_path)
        os.remove(output_path)
        for i in range(snapshots):
            snapshot_path = f"{output_path}_snapshot_{i + 1}.jpg"
            if os.path.exists(snapshot_path):
                os.remove(snapshot_path)

        await progress_message.edit_text("✅ Your video has been processed successfully!")

    except Exception as e:
        await progress_message.edit_text("❌ An error occurred while processing your video.")
        print(f"Error: {e}")






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