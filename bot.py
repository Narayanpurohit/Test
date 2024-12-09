

import os
from pyrogram import Client, filters
from pyrogram.types import Message, InputMediaPhoto
import openai  

# Replace with your actual bot token and credentials
API_ID = "9219444"  # You need to get this from my.telegram.org
API_HASH = "9db23f3d7d8e7fc5144fb4dd218c8cc3"  # You need to get this from my.telegram.org
TOKEN = "7481801715:AAFDx2mtLguQMvYmN4zJBdB-RnC7y2pIR5Y"  # Replace with your bot's token

# Initialize the Pyrogram Client
app = Client("watermark_bot", bot_token=TOKEN, api_id=API_ID, api_hash=API_HASH)

openai.api_key = "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"  

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text(
        "👋 WELCOME to the Watermark Bot!\n\n"
        "Send me a video, and I'll add a watermark to it. You can also configure settings for snapshots, "
        "watermark movement, and more.\n\n"
        "Use /help to see all available commands."
    )



@app.on_message(filters.command("imagine"))  # Triggered by "/imagine" command
async def generate_image(client, message: Message):
    user_message = message.text
    prompt = " ".join(user_message.split()[1:])  # Extract the prompt after the command

    if not prompt:
        await message.reply("Please provide a prompt for the image. Example: `/imagine a cute boy`")
        return

    try:
        # Generate an image using OpenAI's DALL·E API
        response = openai.Image.create(
            prompt=prompt,
            n=1,  # Number of images
            size="512x512"  # Image size
        )
        image_url = response['data'][0]['url']  # Get the image URL

        print("Image generated successfully:", image_url)

        # Send the generated image to the user
        await message.reply_photo(photo=image_url, caption="Here is your generated image!")
    except Exception as e:
        print(f"Error generating image: {e}")
        await message.reply("Sorry, I couldn't generate the image. Please try again later.")



@app.on_message(filters.text)
async def handle_video(client, message: Message):
    user_id = message.from_user.id
    user_message = message.text
    print(user_message)

if __name__ == "__main__":
    app.run()

