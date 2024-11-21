import os
import subprocess
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    filename="watermark_bot.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Replace with your actual bot token
API_ID = "15191874"
API_HASH = "3037d39233c6fad9b80d83bb8a339a07"
TOKEN = "7481801715:AAEV22RePMaDqd2tyxH0clxtnqd5hDpRuTw"

# Initialize the Pyrogram Client
app = Client("watermark_bot", bot_token=TOKEN, api_id=API_ID, api_hash=API_HASH)


def add_watermark(video_path, output_path):
    logging.info(f"Adding watermark to video: {video_path}")
    try:
        # Define watermark texts
        moving_watermark_text = "@PrimeDose"
        static_watermark_text = "Telegram @PrimeDose\nFollow us for updates!"
        top_left_static_text = "@PrimeDose"

        # Get video info
        video_info = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,avg_frame_rate", "-of", "default=noprint_wrappers=1", video_path],
            capture_output=True, text=True
        )
        if video_info.returncode != 0:
            raise Exception(f"Failed to get video info: {video_info.stderr}")

        # Extract FPS, width, and height
        fps = eval(video_info.stdout.split("avg_frame_rate=")[1].split("\n")[0])
        width = int(video_info.stdout.split("width=")[1].split("\n")[0])
        height = int(video_info.stdout.split("height=")[1].split("\n")[0])

        # Get total frames for progress
        frame_count_info = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=nb_frames", "-of", "default=noprint_wrappers=1", video_path],
            capture_output=True, text=True
        )
        total_frames = frame_count_info.stdout.split("=")[-1].strip()
        total_frames = int(total_frames) if total_frames.isdigit() else 0

        # FFmpeg watermark command
        command = [
            "ffmpeg", "-i", video_path,
            "-vf", (
                f"drawtext=text='{moving_watermark_text}':x='if(gte(t,1), mod(t*100, W), NAN)':y=H/2-30:fontsize=20:fontcolor=white,"
                f"drawtext=text='{static_watermark_text}':x=(w-text_w)/2:y=h-80:fontsize=20:fontcolor=white:bordercolor=black:borderw=1,"
                f"drawtext=text='{top_left_static_text}':x=20:y=20:fontsize=20:fontcolor=white:bordercolor=black:borderw=1"
            ),
            "-c:v", "libx264", "-crf", "23", "-preset", "fast", "-c:a", "aac", "-strict", "experimental", "-y", output_path
        ]

        with tqdm(total=total_frames, desc="Processing Video", unit="frame") as pbar:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            while True:
                output = process.stderr.read(1)
                if not output:
                    break
                if b"frame=" in output:
                    pbar.update(1)

        logging.info(f"Watermark added successfully: {output_path}")
        return output_path

    except Exception as e:
        logging.error(f"Error adding watermark: {e}")
        raise


def generate_thumbnail(video_path, width, height):
    logging.info(f"Generating thumbnail for video: {video_path}")
    thumbnail_path = "thumbnail.jpg"

    try:
        if height > width:  # Portrait mode
            subprocess.run(["ffmpeg", "-y", "-i", video_path, "-vframes", "1", "-an", "-s", "320x720", thumbnail_path])
        else:  # Landscape mode
            subprocess.run(["ffmpeg", "-y", "-i", video_path, "-vframes", "1", "-an", "-s", "480x320", thumbnail_path])

        logging.info(f"Thumbnail generated: {thumbnail_path}")
        return thumbnail_path

    except Exception as e:
        logging.error(f"Error generating thumbnail: {e}")
        raise


@app.on_message(filters.command("start"))
async def start(client, update: Message):
    logging.info("Received /start command")
    await update.reply_text("Send me a video and I'll add two watermarks to it! One will move and the other will be static.")


@app.on_message(filters.video)
async def handle_video(client, update: Message):
    logging.info(f"Received video from user: {update.from_user.id}")
    try:
        # Download the video
        video = await update.download()
        input_path = video
        output_path = f"{video}.watermarked.mp4"

        # Add watermarks
        output_video_path = add_watermark(input_path, output_path)

        # Generate thumbnail
        thumbnail_path = generate_thumbnail(input_path, 1920, 1080)

        # Send the watermarked video
        await update.reply_video(output_video_path, thumb=thumbnail_path)

        # Clean up
        os.remove(input_path)
        os.remove(output_video_path)
        os.remove(thumbnail_path)
        logging.info("Temporary files cleaned up successfully.")

    except Exception as e:
        logging.error(f"Error handling video: {e}")
        await update.reply_text(f"An error occurred while processing your video: {e}")


if __name__ == "__main__":
    logging.info("Bot started")
    try:
        app.run()
    except Exception as e:
        logging.critical(f"Bot failed to start: {e}")