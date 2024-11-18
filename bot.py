import os
import cv2
import json
import time
import subprocess
import logging
from pyrogram import Client, filters
from pyrogram.types import Message

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
API_ID = "123456"
API_HASH = "abcde1234567890"
TOKEN = "1234567890:ABCDEFGH"

# Initialize the Pyrogram Client
app = Client("watermark_bot", bot_token=TOKEN, api_id=API_ID, api_hash=API_HASH)

DEFAULT_TEXT = "@kaidamaal"
DEFAULT_POSITION = "bottom-right"


def update_progress_bar(current, total, start_time):
    elapsed_time = time.time() - start_time
    speed = current / (1024 * 1024 * elapsed_time)  # Speed in MB/s
    progress = int(20 * current / total)
    bar = "🟩" * progress + "⬜️" * (20 - progress)
    percentage = (current / total) * 100
    return f"[{bar}] {percentage:.2f}% ({current / (1024 * 1024):.2f} MB/{total / (1024 * 1024):.2f} MB) at {speed:.2f} MB/s"


async def download_file_with_progress(client, message: Message, file_path: str):
    total_size = message.video.file_size
    start_time = time.time()
    async for chunk in client.download_media(
            message, file_name=file_path):
        downloaded_size = os.path.getsize(file_path)
        progress_text = update_progress_bar(downloaded_size, total_size, start_time)
        try:
            await message.reply_text(progress_text, quote=True)
        except:
            pass
    return file_path


async def upload_file_with_progress(client, chat_id, file_path: str, reply_message: Message):
    total_size = os.path.getsize(file_path)
    start_time = time.time()

    async for _ in client.send_video(chat_id, video=file_path, reply_to_message_id=reply_message.message_id):
        uploaded_size = os.path.getsize(file_path)
        progress_text = update_progress_bar(uploaded_size, total_size, start_time)
        try:
            await reply_message.edit_text(progress_text)
        except:
            pass


async def add_watermark_async(input_video, output_video, text=DEFAULT_TEXT, font_scale=0.5, border_thickness=1):
    video = cv2.VideoCapture(input_video)
    fps = video.get(cv2.CAP_PROP_FPS)
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    font = cv2.FONT_HERSHEY_SIMPLEX
    text_size = cv2.getTextSize(text, font, font_scale, border_thickness)[0]
    text_x = 10
    text_y = height - 10

    while True:
        ret, frame = video.read()
        if not ret:
            break

        # Add watermark
        cv2.putText(frame, text, (text_x, text_y), font, font_scale, (0, 0, 255), border_thickness * 4, cv2.LINE_AA)
        cv2.putText(frame, text, (text_x, text_y), font, font_scale, (255, 255, 255), border_thickness, cv2.LINE_AA)
        out.write(frame)

    video.release()
    out.release()


@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text("👋 Welcome! Send me a video to add a watermark.")


@app.on_message(filters.video)
async def handle_video(client, message: Message):
    user_id = message.from_user.id
    progress_message = await message.reply_text("Starting video processing...")

    video_path = f"{user_id}_input.mp4"
    output_path = f"{user_id}_output.mp4"

    # Download video with progress
    await download_file_with_progress(client, message, video_path)

    try:
        # Add watermark
        await add_watermark_async(video_path, output_path)

        # Upload video with progress
        await upload_file_with_progress(client, message.chat.id, output_path, progress_message)
    except Exception as e:
        logger.error(f"Error: {e}")
        await progress_message.edit_text("❌ An error occurred.")
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(output_path):
            os.remove(output_path)


if __name__ == "__main__":
    app.run()