from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
import json
import os
import random
from moviepy.editor import VideoFileClip
from PIL import Image

# Load configuration
from config import API_ID, API_HASH, BOT_TOKEN, USER_DATA_FILE

app = Client("video_merger_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Load or initialize user data
if os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, "r") as file:
        user_data = json.load(file)
else:
    user_data = {}

# Save user data
def save_user_data():
    with open(USER_DATA_FILE, "w") as file:
        json.dump(user_data, file)

# Cancel process handler
@app.on_message(filters.command("cancel"))
async def cancel_process(client, message: Message):
    await message.reply("Operation cancelled.")

# Set upload type handlers
@app.on_message(filters.command("set_video"))
async def set_upload_type_video(client, message: Message):
    user_id = str(message.from_user.id)
    user_data.setdefault(user_id, {})["upload_type"] = "video"
    save_user_data()
    await message.reply("Upload type set to video.")

@app.on_message(filters.command("set_document"))
async def set_upload_type_document(client, message: Message):
    user_id = str(message.from_user.id)
    user_data.setdefault(user_id, {})["upload_type"] = "document"
    save_user_data()
    await message.reply("Upload type set to document.")

# Set intro video handler
@app.on_message(filters.command("set_intro"))
async def set_intro_video(client, message: Message):
    if message.reply_to_message and (message.reply_to_message.video or message.reply_to_message.document):
        file_message = message.reply_to_message
        video_file = await client.download_media(file_message)
        user_id = str(message.from_user.id)
        user_data.setdefault(user_id, {})["video1"] = video_file
        save_user_data()
        await message.reply("Intro video has been set.")
    else:
        await message.reply("Please reply to the video or document you want to set as the intro.")

# Set words to remove from filename handler
@app.on_message(filters.command("set_remove_words"))
async def set_remove_words(client, message: Message):
    user_id = str(message.from_user.id)
    words_to_remove = message.text.split(" ", 1)[1] if " " in message.text else ""
    
    if words_to_remove:
        user_data.setdefault(user_id, {})["remove_words"] = words_to_remove.split(',')
        save_user_data()
        await message.reply(f"Words set to be removed from final filename: {words_to_remove}")
    else:
        await message.reply("Please specify words to remove, separated by commas (e.g., @hub_linkz,@cinemafilx)")

# Helper function to validate video file types (case-insensitive)
def is_supported_video(filename):
    supported_extensions = [".mp4", ".mov", ".avi", ".mkv"]
    return any(filename.lower().endswith(ext) for ext in supported_extensions)

# Merge videos and generate screenshots handler
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
    final_clip = VideoFileClip.concatenate_videoclips([video1_clip, video2_clip])
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

# Help command handler
@app.on_message(filters.command("help"))
async def help_command(client, message: Message):
    help_text = (
        "/set_intro - Set the intro video (use this command in reply to a video).\n"
        "/set_video - Set the default upload type to video.\n"
        "/set_document - Set the default upload type to document.\n"
        "/set_remove_words - Set words to remove from filename (comma-separated).\n"
        "/cancel - Cancel the current operation.\n"
        "/help - Show this help message."
    )
    await message.reply(help_text)

# Run the bot
app.run()