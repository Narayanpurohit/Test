import os
import re
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from imdb import IMDb

# Replace these with your own values
API_ID = 15191874
API_HASH = "3037d39233c6fad9b80d83bb8a339a07"
BOT_TOKEN = "7727908791:AAHUDR2RyXynqjnTgGkeN1zOHf79GanWCqk"

# Directories
IMAGE_DIR = "/www/wwwroot/Jnmovies.site/wp-content/uploads"
IMDB_IMAGE_DIR = "/www/wwwroot/Jnmovies.site/wp-content/uploads/imdb"

# Ensure directories exist
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(IMDB_IMAGE_DIR, exist_ok=True)

# Initialize bot
app = Client("image_host_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def fetch_imdb_image(imdb_url):
    """Fetches the movie title and main poster URL from IMDb using IMDbPY."""
    ia = IMDb()

    # Extract IMDb ID from the URL
    match = re.search(r'tt(\d+)', imdb_url)
    if not match:
        print("Invalid IMDb link format")  # Debugging
        return None, "Invalid IMDb link"

    imdb_id = match.group(1)  # Extract only numeric ID
    print(f"Fetching IMDb data for ID: {imdb_id}")  # Debugging

    try:
        movie = ia.get_movie(imdb_id)
        if not movie or "title" not in movie or "full-size cover url" not in movie:
            print("IMDb data not found")  # Debugging
            return None, "Image not found"

        movie_name = movie["title"].replace(" ", "_")  # Format title
        image_url = movie["full-size cover url"]
        print(f"Movie Name: {movie_name}, Image URL: {image_url}")  # Debugging
        return image_url, movie_name
    except Exception as e:
        print(f"Error fetching IMDb data: {str(e)}")  # Debugging
        return None, f"Error fetching IMDb data: {str(e)}"

def save_imdb_image(image_url, movie_name):
    """Downloads and saves the IMDb image, handling duplicates."""
    ext = image_url.split(".")[-1].split("?")[0]  # Get file extension
    base_name = f"{movie_name}.{ext}"
    save_path = os.path.join(IMDB_IMAGE_DIR, base_name)

    # Avoid duplicate filenames
    counter = 1
    while os.path.exists(save_path):
        save_path = os.path.join(IMDB_IMAGE_DIR, f"{movie_name}_{counter}.{ext}")
        counter += 1

    print(f"Saving IMDb image to: {save_path}")  # Debugging
    response = requests.get(image_url, stream=True)
    if response.status_code == 200:
        with open(save_path, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        return save_path
    return None

@app.on_message(filters.photo)
async def handle_image(client: Client, message: Message):
    """Handles normal image uploads"""
    file_path = await message.download(file_name=os.path.join(IMAGE_DIR, f"{message.photo.file_id}.jpg"))
    
    image_url = f"https://Jnmovies.site/wp-content/uploads/{os.path.basename(file_path)}"
    await message.reply_text(f"Here is your image link: {image_url}")

@app.on_message(filters.text)
async def handle_message(client, message):
    """Handle incoming IMDb links."""
    text = message.text.strip()

    if "imdb.com/title/" in text:
        print(f"Received IMDb link: {text}")  # Debugging
        image_url, movie_name = fetch_imdb_image(text)

        if not image_url:
            await message.reply_text("Could not fetch IMDb image.")
            return

        save_path = save_imdb_image(image_url, movie_name)
        if not save_path:
            await message.reply_text("Failed to download IMDb image.")
            return

        # Construct the image URL
        imdb_image_url = f"https://Jnmovies.site/wp-content/uploads/imdb/{os.path.basename(save_path)}"

        await message.reply_text(f"IMDb Image Saved:\n{imdb_image_url}")

print("Bot is running...")
app.run()