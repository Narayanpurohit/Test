import os
import cv2
import json
import time
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message, InputMediaPhoto

# Replace with your actual bot token and credentials
API_ID = "15191874"  # Get this from my.telegram.org
API_HASH = "3037d39233c6fad9b80d83bb8a339a07"  # Get this from my.telegram.org
TOKEN = "7481801715:AAEV22RePMaDqd2tyxH0clxtnqd5hDpRuTw"  # Replace with your bot's token

# Initialize the Pyrogram Client
app = Client("watermark_bot", bot_token=TOKEN, api_id=API_ID, api_hash=API_HASH)

# Load user settings from file
user_settings = {}
def load_user_settings():
    global user_settings
    if os.path.exists("user_settings.json"):
        with open("user_settings.json", "r") as f:
            user_settings = json.load(f)

# Save user settings to file
def save_user_settings():
    with open("user_settings.json", "w") as f:
        json.dump(user_settings, f)

# Default settings
DEFAULT_TEXT = "jn-bots.in"
DEFAULT_POSITION = "bottom-right"
DEFAULT_SNAPSHOTS = 8

# Function to add a watermark to a video (without audio)
def add_watermark(video_path, output_path, text=DEFAULT_TEXT, position=None,
                  movement="moving", speed=2, direction="horizontal", loop=True, progress_callback=None):
    video = cv2.VideoCapture(video_path)
    fps = video.get(cv2.CAP_PROP_FPS)
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

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
        x, y = 0, height // 2  # Start from the left middle
        dx, dy = (speed, 0) if direction == "horizontal" else (0, speed)
    else:
        # Default static position (if user defines static watermark)
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

    # Combine the processed video with original audio using ffmpeg
    command = [
        "ffmpeg", "-y", "-i", temp_video_path, "-i", video_path, "-c:v", "copy", "-c:a", "aac",
        "-map", "0:v:0", "-map", "1:a:0", output_path
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Clean up temporary file
    os.remove(temp_video_path)

# Function to capture snapshots
def capture_snapshots(video_path, snapshot_count=DEFAULT_SNAPSHOTS):
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
    return snapshots

# Function to generate a thumbnail from the video
def generate_thumbnail(video_path):
    video = cv2.VideoCapture(video_path)
    video.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Set to the first frame
    ret, frame = video.read()
    thumbnail_path = "thumbnail.jpg"
    if ret:
        cv2.imwrite(thumbnail_path, frame)
    video.release()
    return thumbnail_path if ret else None

# Command to start the bot
@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text(
        "👋 WELCOME to the Watermark Bot!\n\n"
        "Send me a video, and I'll add a watermark to it. You can also configure settings for snapshots, "
        "watermark movement, and more.\n\n"
        "Use /help to see all available commands."
    )

# Command to display help
@app.on_message(filters.command("help"))
async def help(client, message: Message):
    await message.reply_text(
        "📜 HELP MENU 📜\n\n"
        "Use the following commands to control the bot:\n\n"
        "/set_watermark <text> - Set custom watermark text.\n"
        "/position <top-left | top-right | bottom-left | bottom-right | center> - Set watermark position.\n"
        "/movement <static | moving> - Set watermark type.\n"
        "/speed <1-10> - Set speed for moving watermark.\n"
        "/direction <horizontal | vertical> - Set direction for moving watermark.\n"
        "/loop <yes | no> - Set if moving watermark loops back.\n"
        "/snapshots <number> - Set the number of snapshots.\n"
        "/snap - Take snapshots from video.\n"
        "/clear - Clear all media files.\n\n"
        "💡 Send a video to start adding watermarks and snapshots!"
    )

from pyrogram.types import InputMediaPhoto

# Command to take snapshots
@app.on_message(filters.command("snap"))
async def snap(client, message: Message):
    # Ensure the command is used in reply to a video message
    if not message.reply_to_message or not message.reply_to_message.video:
        await message.reply_text("⚠️ Please reply to a video message to take snapshots.")
        return

    user_id = message.from_user.id
    snapshot_count = user_settings.get(user_id, {}).get("snapshots", DEFAULT_SNAPSHOTS)

    # Download the video from the replied message
    video = await message.reply_to_message.download()
    
    # Capture snapshots
    snapshots = capture_snapshots(video, snapshot_count)

    # Send snapshots in groups of 10
    MAX_MEDIA_GROUP_SIZE = 10
    for i in range(0, len(snapshots), MAX_MEDIA_GROUP_SIZE):
        media_group = [InputMediaPhoto(photo) for photo in snapshots[i:i + MAX_MEDIA_GROUP_SIZE]]
        await message.reply_media_group(media_group)

    # Clean up snapshots
    for snapshot in snapshots:
        os.remove(snapshot)
# Command to set custom watermark text
@app.on_message(filters.command("set_watermark"))
async def set_watermark(client, message: Message):
    # Ensure that the user provided text after the command
    if len(message.text.split()) < 2:
        await message.reply_text("⚠️ Please provide the watermark text after the command. Example: `/set_watermark YourText`.")
        return

    # Extract the watermark text from the command message
    watermark_text = " ".join(message.text.split()[1:])
    
    user_id = message.from_user.id
    # Update user settings with the new watermark text
    if user_id not in user_settings:
        user_settings[user_id] = {}

    user_settings[user_id]['watermark_text'] = watermark_text
    save_user_settings()

    # Confirm the change to the user
    await message.reply_text(f"✅ Your watermark text has been updated to: {watermark_text}")
# Handle video messages with progress updates
@app.on_message(filters.video | filters.document)
async def handle_video(client, message: Message):
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

    # Download and process the video
    video = await message.download()
    output_path = f"{video}.watermarked.mp4"
    
    # Generate a thumbnail for the video
    thumbnail_path = generate_thumbnail(video)

    # Start watermarking with progress updates
    add_watermark(video, output_path, text, position, movement, speed, direction, loop, progress_callback)

    # Final update after processing
    await progress_message.edit_text("[🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩] 100.00%\nProcessing complete!")

    # Send the processed video with thumbnail if available
    if thumbnail_path and os.path.exists(thumbnail_path):
        await message.reply_video(output_path, thumb=thumbnail_path, supports_streaming=True)
    else:
        await message.reply_video(output_path, supports_streaming=True)

    # Clean up files
    os.remove(video)
    os.remove(output_path)
    if thumbnail_path and os.path.exists(thumbnail_path):
        os.remove(thumbnail_path)

# Load user settings on start
load_user_settings()

if __name__ == "__main__":
    app.run()

