# Replace with your actual bot token and credentials

import os
import cv2
import json
import time
import subprocess
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InputMediaPhoto

# Configure logging
logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Replace with your actual bot token and credentials
API_ID = "9219444"  # Get this from my.telegram.org
API_HASH = "9db23f3d7d8e7fc5144fb4dd218c8cc3"  # Get this from my.telegram.org
TOKEN = "7646833477:AAF_K4lzjzZmaB9LZzRLPfA0Hhr3SfSWOak"  # Replace with your bot's token

# Initialize the Pyrogram Client
app = Client("watermark_bot", bot_token=TOKEN, api_id=API_ID, api_hash=API_HASH)

# Load user settings from file
user_settings = {}
def load_user_settings():
    global user_settings
    try:
        if os.path.exists("user_settings.json"):
            with open("user_settings.json", "r") as f:
                user_settings = json.load(f)
                logging.info("User settings loaded successfully.")
    except Exception as e:
        logging.error(f"Error loading user settings: {e}")

# Save user settings to file
def save_user_settings():
    try:
        with open("user_settings.json", "w") as f:
            json.dump(user_settings, f)
            logging.info("User settings saved successfully.")
    except Exception as e:
        logging.error(f"Error saving user settings: {e}")

# Default settings
DEFAULT_TEXT = "@kaidamaal"
DEFAULT_POSITION = "bottom-right"
DEFAULT_SNAPSHOTS = 12

# Function to add a watermark to a video (with progress logging)
def add_watermark(video_path, output_path, text=DEFAULT_TEXT, position=None,
                  movement="moving", speed=2, direction="horizontal", loop=True, progress_callback=None):
    try:
        video = cv2.VideoCapture(video_path)
        fps = video.get(cv2.CAP_PROP_FPS)
        width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        logging.info(f"Processing video: {video_path} ({total_frames} frames, {fps} FPS)")

        # OpenCV VideoWriter for processing frames without audio
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        temp_video_path = "temp_video_no_audio.mp4"
        out = cv2.VideoWriter(temp_video_path, fourcc, fps, (width, height))

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1
        font_thickness = 2
        text_size = cv2.getTextSize(text, font, font_scale, font_thickness)[0]

        # Set initial position for moving watermark
        if movement == "moving":
            x, y = 0, height // 2
            dx, dy = (speed, 0) if direction == "horizontal" else (0, speed)
        else:
            x, y = {
                "top-left": (10, 30),
                "top-right": (width - text_size[0] - 10, 30),
                "bottom-left": (10, height - 20),
                "bottom-right": (width - text_size[0] - 10, height - 20),
                "center": ((width - text_size[0]) // 2, height // 2),
            }.get(position, (10, 30))

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
            cv2.putText(frame, text, (x, y), font, font_scale, (0, 0, 255), font_thickness * 3, cv2.LINE_AA)
            cv2.putText(frame, text, (x, y), font, font_scale, (255, 255, 255), font_thickness, cv2.LINE_AA)
            out.write(frame)
            frame_count += 1

            # Update progress at intervals
            if progress_callback and time.time() - last_update_time > 1:
                progress_callback(frame_count, total_frames)
                last_update_time = time.time()

        video.release()
        out.release()
        logging.info(f"Video frames processed: {frame_count}/{total_frames}")

        # Combine the processed video with original audio using ffmpeg
        command = [
            "ffmpeg", "-y", "-i", temp_video_path, "-i", video_path, "-c:v", "copy", "-c:a", "aac",
            "-map", "0:v:0", "-map", "1:a:0", output_path
        ]
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        os.remove(temp_video_path)
        logging.info(f"Watermarked video saved: {output_path}")

    except Exception as e:
        logging.error(f"Error during watermarking: {e}")
        raise

# Enhanced progress logging in video processing
@app.on_message(filters.video)
async def handle_video(client, message: Message):
    try:
        user_id = message.from_user.id
        user_data = user_settings.get(user_id, {})
        text = user_data.get('watermark_text', DEFAULT_TEXT)
        position = user_data.get('position', DEFAULT_POSITION)
        movement = user_data.get('movement', 'static')
        speed = user_data.get('speed', 1)
        direction = user_data.get('direction', 'horizontal')
        loop = user_data.get('loop', False)

        progress_message = await message.reply_text("Starting video processing...")

        def progress_callback(current, total):
            progress = int(20 * current / total)
            bar = "🟩" * progress + "⬜️" * (20 - progress)
            client.loop.create_task(progress_message.edit_text(
                f"[{bar}] {current / total * 100:.2f}%\nFrames processed: {current}/{total}"
            ))

        video = await message.download()
        output_path = f"{video}.watermarked.mp4"
        thumbnail_path = generate_thumbnail(video)
        add_watermark(video, output_path, text, position, movement, speed, direction, loop, progress_callback)

        await progress_message.edit_text("[🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩] 100.00%\nProcessing complete!")
        if thumbnail_path and os.path.exists(thumbnail_path):
            await message.reply_video(output_path, thumb=thumbnail_path, supports_streaming=True)
        else:
            await message.reply_video(output_path, supports_streaming=True)

        os.remove(video)
        os.remove(output_path)
        if thumbnail_path and os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)

    except Exception as e:
        logging.error(f"Error handling video message: {e}")
        await message.reply_text("❌ An error occurred while processing the video.")

# Load user settings on start
load_user_settings()

if __name__ == "__main__":
    app.run()