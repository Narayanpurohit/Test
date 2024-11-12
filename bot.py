import os
import json
import random
from pyrogram import Client, filters
from moviepy.editor import VideoFileClip, concatenate_videoclips
from PIL import Image



API_ID = int("26847865")
API_HASH = "0ef9fdd3e5f1ed49d4eb918a07b8e5d6"
BOT_TOKEN = "6529631588:AAGWRMpC8ho7m85SZ1hUQnYEuBZcR8zt6Tw"

app = Client("video_merger_bot", api_id=API_ID, api_hash="API_HASH", bot_token="BOT_TOKEN")

USER_DATA_FILE = "user_data.json"

def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_user_data(data):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

user_data = load_user_data()

def get_user_settings(user_id):
    if str(user_id) not in user_data:
        user_data[str(user_id)] = {
            "video1": None,
            "upload_type": "video",
            "take_screenshots": True
        }
        save_user_data(user_data)
    return user_data[str(user_id)]

@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    get_user_settings(user_id)
    await message.reply("Welcome! Use /config to view and change settings.")

@app.on_message(filters.command("config"))
async def show_config(client, message):
    user_id = message.from_user.id
    user_settings = get_user_settings(user_id)
    config_message = (
        f"**Your Configuration**:\n"
        f"1. **Upload Type**: {user_settings['upload_type']} (use /set_upload_type to change)\n"
        f"2. **Take Screenshots**: {user_settings['take_screenshots']} (use /toggle_screenshots to change)\n"
        f"3. **Intro Video**: {'Set' if user_settings['video1'] else 'Not Set'} (use /set_intro to change)\n"
    )
    await message.reply(config_message)

@app.on_message(filters.command("set_upload_type"))
async def set_upload_type(client, message):
    user_id = message.from_user.id
    user_settings = get_user_settings(user_id)
    new_type = "document" if user_settings["upload_type"] == "video" else "video"
    user_settings["upload_type"] = new_type
    save_user_data(user_data)
    await message.reply(f"Upload type set to {new_type}.")

@app.on_message(filters.command("toggle_screenshots"))
async def toggle_screenshots(client, message):
    user_id = message.from_user.id
    user_settings = get_user_settings(user_id)
    user_settings["take_screenshots"] = not user_settings["take_screenshots"]
    save_user_data(user_data)
    status = "enabled" if user_settings["take_screenshots"] else "disabled"
    await message.reply(f"Screenshots have been {status}.")

@app.on_message(filters.command("set_intro"))
async def set_video1(client, message):
    user_id = message.from_user.id
    if not message.video:
        await message.reply("Please send a video to set as Video1.")
        return

    file = await message.video.download(f"{user_id}_video1.mp4")
    user_data[str(user_id)]["video1"] = file
    save_user_data(user_data)
    await message.reply("Intro video saved as Video1!")

@app.on_message(filters.video)
async def merge_videos_and_screenshots(client, message):
    user_id = message.from_user.id
    user_settings = get_user_settings(user_id)

    video1_path = user_settings["video1"]
    if not video1_path:
        await message.reply("Set an intro video with /set_intro first.")
        return

    video2_path = await message.video.download(f"{user_id}_video2.mp4")
    video1_clip = VideoFileClip(video1_path)
    video2_clip = VideoFileClip(video2_path)
    final_clip = concatenate_videoclips([video1_clip, video2_clip])
    final_video_path = f"{user_id}_merged_video.mp4"
    final_clip.write_videofile(final_video_path)

    screenshots = []
    if user_settings["take_screenshots"]:
        for _ in range(8):
            random_time = random.uniform(0, video2_clip.duration)
            frame = video2_clip.get_frame(random_time)
            screenshot_path = f"{user_id}_screenshot_{int(random_time)}.jpg"
            Image.fromarray(frame).save(screenshot_path)
            screenshots.append(screenshot_path)

    if user_settings["upload_type"] == "video":
        await message.reply_video(video=final_video_path)
    else:
        await message.reply_document(document=final_video_path)

    if user_settings["take_screenshots"]:
        for screenshot in screenshots:
            await message.reply_photo(photo=screenshot)

    video1_clip.close()
    video2_clip.close()
    final_clip.close()
    os.remove(video2_path)
    os.remove(final_video_path)
    for screenshot in screenshots:
        os.remove(screenshot)

app.run()