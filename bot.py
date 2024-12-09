

import os
import cv2
import json
import time
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message, InputMediaPhoto

# Replace with your actual bot token and credentials
API_ID = "9219444"  # You need to get this from my.telegram.org
API_HASH = "9db23f3d7d8e7fc5144fb4dd218c8cc3"  # You need to get this from my.telegram.org
TOKEN = "7481801715:AAFDx2mtLguQMvYmN4zJBdB-RnC7y2pIR5Y"  # Replace with your bot's token

# Initialize the Pyrogram Client
app = Client("watermark_bot", bot_token=TOKEN, api_id=API_ID, api_hash=API_HASH)

# Load user settings from file

    # OpenCV VideoWriter for processing frames without audio
    
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


@app.on_message()
async def handle_video(client, message: Message):
    user_id = message.from_user.id
    print("hii")

if __name__ == "__main__":
    app.run()

