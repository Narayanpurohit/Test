import os
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from tqdm import tqdm  # Import tqdm for progress bar

# Replace with your actual bot token
API_ID = "15191874"
API_HASH = "3037d39233c6fad9b80d83bb8a339a07"
TOKEN = "7481801715:AAEV22RePMaDqd2tyxH0clxtnqd5hDpRuTw"

# Initialize the Pyrogram Client
app = Client("watermark_bot", bot_token=TOKEN, api_id=API_ID, api_hash=API_HASH)


# Progress handler
async def progress_handler(current, total, prefix, update: Message):
    percentage = (current / total) * 100
    progress_bar = "⬢" * int(percentage // 5) + "⬡" * (20 - int(percentage // 5))
    message = (
        f"⚠️ **Please wait...**\n\n"
        f"📥 {prefix}...\n"
        f"╭━━━━❰ᴘʀᴏɢʀᴇss ʙᴀʀ❱━➣\n"
        f"┣⪼ {progress_bar}\n"
        f"┣⪼ 🗃️ **Sɪᴢᴇ:** {current / 1024**2:.2f} MB / {total / 1024**2:.2f} MB\n"
        f"┣⪼ ⏳ **Dᴏɴᴇ:** {percentage:.2f}%\n"
        f"╰━━━━━━━━━━━━━━━➣"
    )
    try:
        await update.edit_text(message)
    except:
        pass


# Add watermark to video
def add_watermark(video_path, output_path):
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
        "-c:v", "libx264", "-crf", "23", "-preset", "fast", "-c:a", "aac", "-strict", "experimental", "-map", "0:v:0", "-map", "0:a?", "-y", output_path
    ]

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(f"FFmpeg error: {stderr.decode()}")
    return output_path


# Generate thumbnail for the video
def generate_thumbnail(video_path):
    thumbnail_path = "thumbnail.jpg"
    subprocess.run(["ffmpeg", "-y", "-i", video_path, "-vframes", "1", "-s", "480x320", thumbnail_path])
    return thumbnail_path


@app.on_message(filters.command("start"))
async def start(client, update: Message):
    await update.reply_text("Send me a video, and I'll add two watermarks to it! One will move, and the other will be static.")


@app.on_message(filters.video)
async def handle_video(client, update: Message):
    # Acknowledge receipt
    status = await update.reply_text("⚠️ **Please wait...**\n\n📥 **Dᴏᴡɴʟᴏᴀᴅ Sᴛᴀʀᴛᴇᴅ...**")

    # Download video
    video = await client.download_media(update.video.file_id, progress=progress_handler, progress_args=("Dᴏᴡɴʟᴏᴀᴅɪɴɢ", status))

    # Paths
    input_path = video
    output_path = f"{os.path.splitext(video)[0]}_watermarked.mp4"

    # Processing video
    await status.edit_text("⚠️ **Please wait...**\n\n🎞️ **Aᴅᴅɪɴɢ ᴡᴀᴛᴇʀᴍᴀʀᴋ...**")
    output_video_path = add_watermark(input_path, output_path)

    # Generate thumbnail
    thumbnail_path = generate_thumbnail(output_video_path)

    # Upload video
    await status.edit_text("⚠️ **Please wait...**\n\n📤 **Uᴘʟᴏᴀᴅɪɴɢ ᴠɪᴅᴇᴏ...**")
    await update.reply_document(
        document=output_video_path,
        thumb=thumbnail_path,
        caption="✅ **Here is your watermarked video!**",
        progress=progress_handler,
        progress_args=("Uᴘʟᴏᴀᴅɪɴɢ", status)
    )

    # Clean up
    os.remove(input_path)
    os.remove(output_video_path)
    os.remove(thumbnail_path)
    await status.delete()


if __name__ == "__main__":
    app.run()