import os
import re
import pymongo
import requests
from motor.motor_asyncio import AsyncIOMotorClient
from imdb import Cinemagoer
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ✅ Import configuration from config.py
from config import API_ID, API_HASH, BOT_TOKEN, MONGO_URI, DB_NAME, COLLECTION_NAME, DEFAULT_POST_TEMPLATE, DEFAULT_FOOTER_TEMPLATE

# 🔹 MongoDB Setup
client_mongo = AsyncIOMotorClient(MONGO_URI)
db = client_mongo[DB_NAME]
users_collection = db[COLLECTION_NAME]

# 🔹 IMDbPY Setup
ia = Cinemagoer()

# 🔹 Pyrogram Bot Setup
app = Client(
    "imdb_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

UPLOAD_FOLDER = "/www/wwwroot/jnmovies.site/wp-content/uploads/"  # Path to save images

def sanitize_filename(filename):
    """Sanitize filename to avoid issues with special characters."""
    return filename.replace(" ", "_").replace("/", "_")

def get_unique_filename(directory, filename):
    """Ensure filename is unique by appending a number if needed."""
    base_name, ext = os.path.splitext(filename)
    counter = 1
    while os.path.exists(os.path.join(directory, filename)):
        filename = f"{base_name}_{counter}{ext}"
        counter += 1
    return filename

async def get_user_data(user_id):
    """Fetch user data from MongoDB or create a new entry."""
    user = await users_collection.find_one({"user_id": user_id})
    if not user:
        user = {
            "user_id": user_id,
            "post_template": DEFAULT_POST_TEMPLATE,
            "footer_template": DEFAULT_FOOTER_TEMPLATE
        }
        await users_collection.insert_one(user)
    return user

@app.on_message(filters.command("start"))
async def start_command(client, message):
    """Handle the /start command."""
    user_id = message.from_user.id
    await get_user_data(user_id)  # Ensure user is stored in the database
    await message.reply_text("Hi! Use /newpost to generate a movie post!")

@app.on_message(filters.command("newpost"))
async def newpost_command(client, message):
    """Start new post creation."""
    user_id = message.from_user.id
    await message.reply_text("🎬 Send me the **IMDb link**:")
    imdb_link = (await client.listen(message.chat.id)).text.strip()
    await collect_post_details(client, message, user_id, imdb_link)

async def collect_post_details(client, message, user_id, imdb_link):
    """Collect all post details step by step."""

    await message.reply_text("🎧 Send me the **Audio Languages** (e.g., Hindi, English, Tamil):")
    audios = (await client.listen(message.chat.id)).text.strip()

    await message.reply_text("🎭 Send me the **Category** (e.g., Hollywood, Bollywood, Anime, etc.):")
    category = (await client.listen(message.chat.id)).text.strip()

    await message.reply_text("🎞 Send me the **Quality**:")
    quality = (await client.listen(message.chat.id)).text.strip()

    await message.reply_text("📌 Send me the **Post Type** (e.g., Movie, Web Series, etc.):")
    type = (await client.listen(message.chat.id)).text.strip()

    await message.reply_text("🖼 Send me the **Screenshot Links** (each on a new line):")
    screenshots = (await client.listen(message.chat.id)).text.strip().split("\n")

    await message.reply_text("🔗 Send the **Download Links** in this format:\n"
                             "`Resolution | Size | Download Link | Stream Link`\n"
                             "You can send multiple lines.")
    download_links = (await client.listen(message.chat.id)).text.strip().split("\n")
    m = await message.reply_sticker("CAACAgQAAxkBAAEKeqNlIpmeUoOEsEWOWEiPxPi3hH5q-QACbg8AAuHqsVDaMQeY6CcRojAE")

    await generate_post(client, message, user_id, imdb_link, audios, category, quality, type, screenshots, download_links)

async def generate_post(client, message, user_id, imdb_url, audios, category, quality, type, screenshots, download_links):
    """Generate a post using all collected details and download IMDb poster."""

    user = await get_user_data(user_id)
    post_template = user["post_template"]
    footer_template = user["footer_template"]

    imdb_id_match = re.search(r'tt(\d+)', imdb_url)
    imdb_id = imdb_id_match.group(1) if imdb_id_match else None
    if not imdb_id:
        await message.reply_text("⚠️ Invalid IMDb link!")
        return

    movie = ia.get_movie(imdb_id)
    poster_url = movie.get('full-size cover url', 'No poster available')
    title = movie.get('title', 'Unknown Title')
    rating = movie.get('rating', 'No Rating')
    year = movie.get('year', 'Unknown Year')
    genres = ", ".join(movie.get('genres', []))
    plot = movie.get('plot', ['Plot not available'])[0]
    cast_list = ", ".join([str(cast) for cast in movie.get('cast', [])[:5]]) or "N/A"
    writers = ", ".join([str(writer) for writer in movie.get('writer', [])[:3]]) or "N/A"
    directors = ", ".join([str(director) for director in movie.get('director', [])[:3]]) or "N/A"

    # **Download IMDb Poster AFTER collecting all details**
    if poster_url.startswith("http"):
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            response = requests.get(poster_url, stream=True, headers=headers, verify=False)
            if response.status_code == 200:
                file_name = sanitize_filename(f"{title}.jpg")
                file_name = get_unique_filename(UPLOAD_FOLDER, file_name)
                file_path = os.path.join(UPLOAD_FOLDER, file_name)
                with open(file_path, "wb") as file:
                    for chunk in response.iter_content(1024):
                        file.write(chunk)
                poster_url = f"https://jnmovies.site/wp-content/uploads/{file_name}"
            else:
                poster_url = "No poster available"
        except Exception as e:
            poster_url = "No poster available"

    # **Generate Screenshot Links in HTML**
    screenshots_html = '<div class="neoimgs"><div class="screenshots"><ul class="neoscr">\n'
    for link in screenshots:
        screenshots_html += f'<li class="neoss"><img src="{link}" /></li>\n'
    screenshots_html += '</ul></div></div>'

    # **Generate Download Buttons**
    download_html = ""
    for line in download_links:
        parts = line.split("|")
        if len(parts) == 4:
            resolution, size, dl_link, stream_link = map(str.strip, parts)
            download_html += f'<h6 style="text-align: center;"><strong>{title} ({year}) {resolution} [{size}]</strong></h6>\n'
            download_html += f'<p style="text-align: center;"><a href="{dl_link}">Download</a> | <a href="{stream_link}">Stream</a></p>\n'

    post = post_template.format(poster_url=poster_url, title=title, year=year, genres=genres, plot=plot, quality=quality, audios=audios, category=category, type=type, imdb_id=imdb_id, directors=directors, writers=writers, cast_list=cast_list, rating=rating)
    html_content = post + "\n\n" + screenshots_html + "\n\n" + download_html + footer_template

    file_path = "movie_details.html"
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(html_content)
    await m.delete()
    await client.send_document(message.chat.id, file_path, caption="📄 Here is your movie details file.")
    os.remove(file_path)

if __name__ == "__main__":
    print("Bot is running...")
    app.run()