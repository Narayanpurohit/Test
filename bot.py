
# Load configuration
from config import API_ID, API_HASH, BOT_TOKEN, USER_DATA_FILE


import os
import random
from pyrogram import Client, filters
from pyrogram.types import Message
from moviepy.editor import VideoFileClip, concatenate_videoclips
from PIL import Image

API_ID = "YOUR_API_ID"
API_HASH = "YOUR_API_HASH"
BOT_TOKEN = "YOUR_BOT_TOKEN"

# Initialize bot
app = Client("video_merger_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Dictionary to store user configurations
user_data = {}

# Helper functions
def is_supported_video(filename):
    return filename.lower().endswith((".mp4", ".mov", ".avi", ".mkv"))

# Command to set intro video
@app.on_message(filters.command("set_intro") & filters.reply)
async def set_intro(client, message: Message):
    if message.reply_to_message.video or message.reply_to_message.document:
        file_message = message.reply_to_message.video or message.reply_to_message.document
        if is_supported_video(file_message.file_name):
            intro_path = await client.download_media(file_message)
            user_data[message.from_user.id] = user_data.get(message.from_user.id, {})
            user_data[message.from_user.id]["video1"] = intro_path
            await message.reply("Intro video has been set!")
        else:
            await message.reply("Please reply to a valid video file.")
    else:
        await message.reply("Please reply to a video file to set as intro.")

# Command to set upload type
@app.on_message(filters.command("set_video"))
async def set_upload_video(client, message: Message):
    user_data[message.from_user.id] = user_data.get(message.from_user.id, {})
    user_data[message.from_user.id]["upload_type"] = "video"
    await message.reply("Default upload type set to video.")

@app.on_message(filters.command("set_document"))
async def set_upload_document(client, message: Message):
    user_data[message.from_user.id] = user_data.get(message.from_user.id, {})
    user_data[message.from_user.id]["upload_type"] = "document"
    await message.reply("Default upload type set to document.")

# Command to set words to remove from file name
@app.on_message(filters.command("set_remove_words"))
async def set_remove_words(client, message: Message):
    words = message.text.split(maxsplit=1)[1].split(",")
    user_data[message.from_user.id] = user_data.get(message.from_user.id, {})
    user_data[message.from_user.id]["remove_words"] = [word.strip() for word in words]
    await message.reply("Words to remove from filename have been set.")

# Command to merge videos and generate screenshots
@app.on_message(filters.video | filters.document)
async def merge_videos(client, message: Message):
    user_id = str(message.from_user.id)
    
    # Check if an intro video exists
    if user_id not in user_data or "video1" not in user_data[user_id]:
        await message.reply("You need to set an intro video first using /set_intro.")
        return
    
    # Download the main video (video2)
    file_message = message.video or message.document
    if file_message and is_supported_video(file_message.file_name):
        video2_file = await client.download_media(file_message)
    else:
        await message.reply("Please send a valid video file format (e.g., .mp4, .mov, .avi, .mkv).")
        return

    # Load the intro video (video1)
    video1_file = user_data[user_id]["video1"]
    video1_clip = VideoFileClip(video1_file)
    video2_clip = VideoFileClip(video2_file)

    # Determine filename for the final video
    final_filename = file_message.file_name
    
    # Remove specified words from the final filename
    words_to_remove = user_data.get(user_id, {}).get("remove_words", [])
    for word in words_to_remove:
        final_filename = final_filename.replace(word, "")
    
    final_filename = final_filename.strip()  # Remove any extra spaces from the filename
    output_path = os.path.join(f"{user_id}_{final_filename}")

    # Concatenate videos
    final_clip = concatenate_videoclips([video1_clip, video2_clip])
    final_clip.write_videofile(output_path, codec="libx264")

    # Generate screenshots
    screenshots = []
    for _ in range(8):
        random_time = random.uniform(0, video2_clip.duration)
        frame = video2_clip.get_frame(random_time)
        image = Image.fromarray(frame)
        screenshot_path = f"{user_id}_screenshot_{int(random_time)}.jpg"
        image.save(screenshot_path)
        screenshots.append(screenshot_path)

    # Determine upload type
    upload_type = user_data.get(user_id, {}).get("upload_type", "video")
    
    # Send merged video
    if upload_type == "video":
        await message.reply_video(output_path)
    else:
        await message.reply_document(output_path)
    
    # Send screenshots
    for screenshot in screenshots:
        await message.reply_photo(screenshot)

    # Clean up
    os.remove(video2_file)
    os.remove(output_path)
    for screenshot in screenshots:
        os.remove(screenshot)

# Help command
@app.on_message(filters.command("help"))
async def help_command(client, message: Message):
    help_text = """
/set_intro - Set the intro video by replying to a video file.
/set_video - Set the upload type to video.
/set_document - Set the upload type to document.
/set_remove_words - Set words to remove from filenames (comma-separated).
To merge videos, send a video file after setting your intro.
"""
    await message.reply(help_text)

# Start command
@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    await message.reply("Welcome! Use /help to see available commands.")

if __name__ == "__main__":
    app.run()