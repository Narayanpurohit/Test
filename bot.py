
import os
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from tqdm import tqdm  # Import tqdm for progress bar

# Replace with your actual bot token
API_ID = "9219444"  # You need to get this from my.telegram.org
API_HASH = "9db23f3d7d8e7fc5144fb4dd218c8cc3"  # You need to get this from my.telegram.org
TOKEN = "6677023637:AAEKFwGAWi7hXY2NvAcXBJInZQRIVXmL5CM"  # Replace with your bot's token

# Initialize the Pyrogram Client
app = Client("watermark_bot", bot_token=TOKEN, api_id=API_ID, api_hash=API_HASH)

def add_watermark(video_path, output_path):
    # Define watermark texts
    moving_watermark_text = "jn-bots.in"  # Moving watermark text
    static_watermark_text = "download/watch movies and web series at jn-bots.in"  # Static watermark text with line break
    top_left_static_text = "jn-bots.in"  # Top-left watermark text

    # Get video information (fps, width, height) for progress bar
    video_info = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,avg_frame_rate", "-of", "default=noprint_wrappers=1", video_path],
        capture_output=True, text=True
    )
    fps = eval(video_info.stdout.split("avg_frame_rate=")[1].split("\n")[0])
    width = int(video_info.stdout.split("width=")[1].split("\n")[0])
    height = int(video_info.stdout.split("height=")[1].split("\n")[0])

    # Get total number of frames in the video for progress bar
    frame_count_info = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=nb_frames", "-of", "default=noprint_wrappers=1", video_path],
        capture_output=True, text=True
    )

    # Check if frame count info contains valid data or "N/A"
    frame_count_output = frame_count_info.stdout.strip().split("=")
    if len(frame_count_output) > 1:
        frame_count_str = frame_count_output[1]
        if frame_count_str != "N/A":
            total_frames = int(frame_count_str)
        else:
            total_frames = 0  # If "N/A", set total frames to 0, or handle as needed
    else:
        total_frames = 0  # Fallback to 0 if no frame count is found

    # FFmpeg command to overlay watermark
    command = [
        "ffmpeg", "-i", video_path,
        "-vf", (
            f"drawtext=text='{moving_watermark_text}':x='if(gte(t,1), mod(t*100, W), NAN)':y=H/2-30:fontsize=20:fontcolor=white,"
            f"drawtext=text='{static_watermark_text}':x=(w-text_w)/2:y=h-80:fontsize=20:fontcolor=white:bordercolor=black:borderw=1,"
            f"drawtext=text='{top_left_static_text}':x=20:y=20:fontsize=20:fontcolor=white:bordercolor=black:borderw=1"
        ),
        "-c:v", "libx264", "-crf", "23", "-preset", "fast", "-c:a", "aac", "-strict", "experimental", "-y", output_path
    ]

    # Process video with progress bar
    with tqdm(total=total_frames, desc="Processing Video", unit="frame") as pbar:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while True:
            output = process.stderr.read(1)
            if not output:
                break
            if b"frame=" in output:
                pbar.update(1)

    return output_path

def generate_thumbnail(video_path, width, height):
    """
    Generates a thumbnail for the video. The thumbnail is in portrait mode
    if the video is portrait, otherwise, it is in landscape mode.
    """
    thumbnail_path = "thumbnail.jpg"

    if height > width:  # Portrait mode
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path, "-vframes", "1", "-an", "-s", "320x720", thumbnail_path
        ])
    else:  # Landscape mode
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path, "-vframes", "1", "-an", "-s", "480x320", thumbnail_path
        ])

    return thumbnail_path

@app.on_message(filters.command("start"))
async def start(client, update: Message):  # Accept both 'client' and 'update'
    await update.reply_text("Send me a video and I'll add two watermarks to it! One will move and the other will be static.")

@app.on_message(filters.video)
async def handle_video(client, update: Message):
    # Get the video file
    pm = await update.reply_text("📥 Downloading your video...")
    video = await update.download()
    await pm.edit_text("📤 adding watermark to your video...")

    # Generate paths for input and output
    input_path = video
    output_path = f"{video}.watermarked.mp4"  # Ensure .mp4 extension for output

    # Add both moving and static watermarks to the video and keep audio
    output_video_path = add_watermark(input_path, output_path)

    # Generate a thumbnail for the video
    thumbnail_path = generate_thumbnail(input_path, 1920, 1080)  # You can adjust the width/height

    # Send the watermarked video back to the user with thumbnail
    await pm.edit_text("📤 Uploading your watermarked video...")
    await update.reply_video(output_video_path, thumb=thumbnail_path)

    # Clean up the temporary files
    os.remove(input_path)
    os.remove(output_video_path)
    os.remove(thumbnail_path)  # Remove the generated thumbnail after use

if __name__ == "__main__":
    app.run()

