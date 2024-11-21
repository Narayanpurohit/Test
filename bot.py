import os
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from tqdm import tqdm
from time import time

# Replace with your actual bot token
API_ID = "15191874"
API_HASH = "3037d39233c6fad9b80d83bb8a339a07"
TOKEN = "7481801715:AAEV22RePMaDqd2tyxH0clxtnqd5hDpRuTw"

# Initialize the Pyrogram Client
app = Client("watermark_bot", bot_token=TOKEN, api_id=API_ID, api_hash=API_HASH)

def format_progress(current, total, speed, eta):
    """Generates a progress bar for download and upload."""
    percent = (current / total) * 100
    bar = "⬢" * int(percent / 5) + "⬡" * (20 - int(percent / 5))
    return (
        f"⬢⬢⬢⬢⬢⬢⬢⬢⬢⬢⬡⬡⬡⬡⬡⬡⬡⬡⬡⬡\n"
        f"╭━━━━❰ᴘʀᴏɢʀᴇss ʙᴀʀ❱━➣\n"
        f"┣⪼ 🗃️ Sɪᴢᴇ: {current / 1024 / 1024:.2f} Mʙ | {total / 1024 / 1024:.2f} Mʙ\n"
        f"┣⪼ ⏳️ Dᴏɴᴇ : {percent:.2f}%\n"
        f"┣⪼ 🚀 Sᴩᴇᴇᴅ: {speed / 1024 / 1024:.2f} Mʙ/s\n"
        f"┣⪼ ⏰️ Eᴛᴀ: {eta}s\n"
        f"╰━━━━━━━━━━━━━━━➣"
    )

async def progress_handler(current, total, message, start_time):
    """Tracks and updates progress for download or upload."""
    elapsed_time = time() - start_time
    speed = current / elapsed_time if elapsed_time > 0 else 0
    eta = int((total - current) / speed) if speed > 0 else 0

    progress_text = format_progress(current, total, speed, eta)
    await message.edit_text(f"⚠️Please wait...\n\n☃️ Dᴏᴡɴʟᴏᴀᴅ Sᴛᴀʀᴛᴇᴅ....\n\n{progress_text}")

def add_watermark(video_path, output_path):
    """Adds watermarks to a video."""
    moving_watermark_text = "@PrimeDose"
    static_watermark_text = "Telegram @PrimeDose\nFollow us for updates!"
    top_left_static_text = "@PrimeDose"

    command = [
        "ffmpeg", "-i", video_path,
        "-vf", (
            f"drawtext=text='{moving_watermark_text}':x='if(gte(t,1), mod(t*100, W), NAN)':y=H/2-30:fontsize=20:fontcolor=white,"
            f"drawtext=text='{static_watermark_text}':x=(w-text_w)/2:y=h-80:fontsize=20:fontcolor=white:bordercolor=black:borderw=1,"
            f"drawtext=text='{top_left_static_text}':x=20:y=20:fontsize=20:fontcolor=white:bordercolor=black:borderw=1"
        ),
        "-c:v", "libx264", "-crf", "23", "-preset", "fast", "-c:a", "aac", "-strict", "experimental", "-y", output_path
    ]

    with tqdm(total=100, desc="Processing Video", unit="frame") as pbar:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while True:
            output = process.stderr.read(1)
            if not output:
                break
            if b"frame=" in output:
                pbar.update(1)

    return output_path

@app.on_message(filters.command("start"))
async def start(client, update: Message):
    await update.reply_text("Send me a video and I'll add two watermarks to it! One will move and the other will be static.")

@app.on_message(filters.video)
async def handle_video(client, update: Message):
    message = await update.reply_text("⚠️Please wait...\n\n☃️ Dᴏᴡɴʟᴏᴀᴅ Sᴛᴀʀᴛᴇᴅ....")
    start_time = time()

    # Download the video with progress
    video = await client.download_media(
        message=update.video.file_id,
        progress=progress_handler,
        progress_args=(message, start_time)
    )

    # Paths for input and output
    input_path = video
    output_path = f"{video}.watermarked.mp4"

    # Add watermarks
    await message.edit_text("⚠️Please wait...\n\n✨ Aᴅᴅɪɴɢ ᴡᴀᴛᴇʀᴍᴀʀᴋ....")
    add_watermark(input_path, output_path)

    # Upload the watermarked video
    await message.edit_text("⚠️Please wait...\n\n⬆️ Uᴘʟᴏᴀᴅɪɴɢ ᴠɪᴅᴇᴏ....")
    start_time = time()
    await client.send_document(
        chat_id=update.chat.id,
        document=output_path,
        progress=progress_handler,
        progress_args=(message, start_time)
    )

    # Cleanup
    os.remove(input_path)
    os.remove(output_path)

    await message.edit_text("✅ Done!")

if __name__ == "__main__":
    app.run()