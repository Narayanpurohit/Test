

# Replace with your actual bot token and credentials


import os
import cv2
import json
import time
import subprocess
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InputMediaPhoto

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),  # Log to a file
        logging.StreamHandler()         # Log to console
    ]
)

logger = logging.getLogger(__name__)

# Replace with your actual bot token and credentials
API_ID = "15191874"
API_HASH = "3037d39233c6fad9b80d83bb8a339a07"
TOKEN = "7481801715:AAEV22RePMaDqd2tyxH0clxtnqd5hDpRuTw"

# Initialize the Pyrogram Client
app = Client("watermark_bot", bot_token=TOKEN, api_id=API_ID, api_hash=API_HASH)

# Load user settings from file
user_settings = {}


def load_user_settings():
    global user_settings
    if os.path.exists("user_settings.json"):
        with open("user_settings.json", "r") as f:
            user_settings = json.load(f)
    logger.info("User settings loaded.")


def save_user_settings():
    with open("user_settings.json", "w") as f:
        json.dump(user_settings, f)
    logger.info("User settings saved.")


# Default settings
DEFAULT_TEXT = "@kaidamaal"
DEFAULT_POSITION = "bottom-right"
DEFAULT_SNAPSHOTS = 12



async def add_watermark_async(
    video_path,
    output_path,
    text="Watermark",            # Default watermark text
    position="bottom-right",     # Default position
    border_color=(0, 0, 0),      # Black border
    text_color=(255, 255, 255),  # White text
    font_scale=0.5,              # Adjust text size
    font_thickness=1,            # Thickness of text
    border_thickness=2,          # Thickness of border
    progress_message=None
):
    video = cv2.VideoCapture(video_path)
    fps = video.get(cv2.CAP_PROP_FPS)
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    temp_video_path = "temp_video_no_audio.mp4"
    out = cv2.VideoWriter(temp_video_path, fourcc, fps, (width, height))

    # Define text size for positioning
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_size = cv2.getTextSize(text, font, font_scale, font_thickness)[0]

    # Define positions
    positions = {
        "top-left": (10, 30),
        "top-center": ((width - text_size[0]) // 2, 30),
        "top-right": (width - text_size[0] - 10, 30),
        "center-left": (10, (height + text_size[1]) // 2),
        "center": ((width - text_size[0]) // 2, (height + text_size[1]) // 2),
        "center-right": (width - text_size[0] - 10, (height + text_size[1]) // 2),
        "bottom-left": (10, height - 20),
        "bottom-center": ((width - text_size[0]) // 2, height - 20),
        "bottom-right": (width - text_size[0] - 10, height - 20),
    }

    # Get position coordinates
    x, y = positions.get(position, positions["bottom-right"])  # Default to bottom-right

    frame_count = 0
    last_update_time = time.time()

    while True:
        ret, frame = video.read()
        if not ret:
            break

        # Add static watermark with customizable border and text color
        cv2.putText(frame, text, (x, y), font, font_scale, border_color, border_thickness, cv2.LINE_AA)  # Border
        cv2.putText(frame, text, (x, y), font, font_scale, text_color, font_thickness, cv2.LINE_AA)  # Text
        out.write(frame)
        frame_count += 1

        # Update progress
        if progress_message and time.time() - last_update_time > 1:
            progress = int(20 * frame_count / total_frames)
            bar = "●" * progress + "○" * (20 - progress)
            await progress_message.edit_text(
                f"[{bar}] {frame_count / total_frames * 100:.2f}%\nFrames processed: {frame_count}/{total_frames}"
            )
            last_update_time = time.time()

    video.release()
    out.release()

    # Merge video with original audio
    command = [
        "ffmpeg", "-y", "-i", temp_video_path, "-i", video_path, "-c:v", "copy", "-c:a", "aac",
        "-map", "0:v:0", "-map", "1:a:0", output_path
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    os.remove(temp_video_path)

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text("👋 Welcome! Send me a video to add a watermark.")


@app.on_message(filters.video)
async def handle_video(client, message: Message):
    logger.info(f"Processing video for user: {message.from_user.id}")
    user_id = message.from_user.id
    text = user_settings.get(user_id, {}).get('watermark_text', DEFAULT_TEXT)
    position = user_settings.get(user_id, {}).get('position', DEFAULT_POSITION)

    progress_message = await message.reply_text("Starting video processing...")

    video = await message.download()
    output_path = f"{video}.watermarked.mp4"

    try:
        await add_watermark_async(video, output_path, text, position, progress_message=progress_message)
        await progress_message.edit_text("✅ Processing complete!")
        await message.reply_video(output_path, supports_streaming=True)
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        await progress_message.edit_text("❌ An error occurred while processing the video.")
    finally:
        os.remove(video)
        if os.path.exists(output_path):
            os.remove(output_path)


load_user_settings()

if __name__ == "__main__":
    app.run()