#mogodb post template footer

import os
import re
import pymongo
from motor.motor_asyncio import AsyncIOMotorClient
from imdb import Cinemagoer
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
# ✅ Import configuration from config.py
from config import API_ID, API_HASH, BOT_TOKEN, MONGO_URI, DB_NAME, COLLECTION_NAME, DEFAULT_POST_TEMPLATE, DEFAULT_FOOTER_TEMPLATE,WORDPRESS_URL, WORDPRESS_USERNAME, WORDPRESS_APP_PASSWORD

DOWNLOAD_DIR = "/www/wwwroot/Jnmovies.site/wp-content/uploads/"
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

async def post_to_wordpress(file_path, title):
    # Read file content
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    # Prepare the data for the post
    post_data = {
        "title": title,
        "content": content,
        "status": "publish"  # Set to "draft" if you don't want to publish immediately
    }

    # Make the request to WordPress
    response = requests.post(
        WORDPRESS_URL,
        json=post_data,
        auth=(WORDPRESS_USERNAME, WORDPRESS_APP_PASSWORD),
        headers={"Content-Type": "application/json"}
    )

    # Check the response
    if response.status_code == 201:
        return response.json().get("link")  # Return the post URL
    else:
        return f"Error: {response.text}"


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

def download_image(url, file_name):
    response = requests.get(url)
    if response.status_code == 200:
        file_path = os.path.join(DOWNLOAD_DIR, file_name)
        with open(file_path, "wb") as file:
            file.write(response.content)
        return file_path
    return None



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
    print(imdb_link)
    

    await collect_post_details(client, message, user_id, imdb_link)


async def collect_post_details(client, message, user_id, imdb_link):
    """Collect all post details step by step."""
    await message.reply_text("🎧 Send me the **Movie main poster** :")
    image = (await client.listen(message.chat.id)).text.strip()


    # Step 1: Ask for audios Language
    await message.reply_text("🎧 Send me the **audios Languages** (e.g., Hindi, English, Tamil):")
    audios = (await client.listen(message.chat.id)).text.strip()

    # Step 2: Ask for Category
    await message.reply_text("🎭 Send me the **Category** (e.g., Hollywood, Bollywood, Anime, etc.):")
    category = (await client.listen(message.chat.id)).text.strip()

    # Step 3: Ask for Quality
    await message.reply_text(
        "🎞 Send me the **Quality** (Choose from below):\n"
        "`CAM, HDCAM, TS, HDTS, WEBRip, WEB-DL, HDTV, PDTV, DVDScr, DVDRip, BDRip, BRRip, REMUX, HDRip, 4K UHD BluRay Rip, Lossless`"
    )
    quality = (await client.listen(message.chat.id)).text.strip()

    # Step 4: Ask for Post Type
    await message.reply_text("📌 Send me the **Post Type** (e.g., Movie, Web Series, etc.):")
    type = (await client.listen(message.chat.id)).text.strip()

    # Step 5: Ask for Screenshot Links
    await message.reply_text("🖼 Send me the **Screenshot Links** (each on a new line):")
    screenshots = (await client.listen(message.chat.id)).text.strip().split("\n")

    # Step 6: Ask for Download & Stream Links
    await message.reply_text("🔗 Send the **Download Links** in this format:\n"
                             "`Resolution | Size | Download Link | Stream Link`\n"
                             "You can send multiple lines.")
    download_links = (await client.listen(message.chat.id)).text.strip().split("\n")
    m=await message.reply_sticker("CAACAgQAAxkBAAEKeqNlIpmeUoOEsEWOWEiPxPi3hH5q-QACbg8AAuHqsVDaMQeY6CcRojAE")

    # Now generate the post
    await generate_post(client, message, user_id, imdb_link, audios, category, quality, type, screenshots, download_links,image)


async def generate_post(client, message, user_id, imdb_url, audios, category, quality, type, screenshots, download_links,image):
    """Generate a post using all collected details."""

    # Get user templates
    user = await get_user_data(user_id)
    post_template = user["post_template"]
    footer_template = user["footer_template"]

    # Extract IMDb ID
    imdb_id_match = re.search(r'tt(\d+)', imdb_url)
    imdb_id = imdb_id_match.group(1) if imdb_id_match else None
    if not imdb_id:
        await message.reply_text("⚠️ Invalid IMDb link!")
        return

    # Fetch movie details
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

    title2 = movie.get("title", "unknown_title").replace(" ", "_").replace("/", "_")
    await client.send_message(message.chat.id,f"{title2}")
    file_name = f"{title2}.jpg"
    file_path = os.path.join(DOWNLOAD_DIR, file_name)
    if os.path.exists(file_path):
        poster_url=f"https://jnmovies.site/wp-content/uploads/{file_name}"
        print("hii")
        
    elif poster_url:
        
        if file_path:
            poster_url=f"https://jnmovies.site/wp-content/uploads/{file_name}"
            print(poster_url)
            print("hello")


        else:
            await message.reply_text("Failed to download the poster. Please try again.")
    else:
        await message.reply_text("No poster found for this movie.")
   

    
    print(poster_url)
    print("hlo")
        
    # Generate Screenshot Links in HTML
    screenshots_html = '<div class="neoimgs"><div class="screenshots"><ul class="neoscr">\n'
    for link in screenshots:
        screenshots_html += f'<li class="neoss"><img src="{link}" /></li>\n'
    screenshots_html += '</ul></div></div>'

    # Generate Download Buttons
    download_html = ""
    for line in download_links:
        parts = line.split("|")
        if len(parts) == 4:
            resolution, size, dl_link, stream_link = map(str.strip, parts)
            download_html += f'<h6 style="text-align: center;"><strong>{title} ({year}) {resolution} [{size}]</strong></h6>\n'
            download_html += f'<p style="text-align: center;"><a href="{dl_link}">Download</a> | <a href="{stream_link}">Stream</a></p>\n'

    # Fill the template
    post = post_template.format(poster_url=poster_url,title=title, year=year, genres=genres, plot=plot, quality=quality,audios=audios, category=category,type=type,imdb_id=imdb_id,directors =directors,writers=writers,cast_list=cast_list,rating=rating,image=image )
    html_content = post + "\n\n" + screenshots_html + "\n\n" + download_html + footer_template

    # Save to a .html file
    file_path = "movie_details.html"
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(html_content)
    

    await client.send_document(message.chat.id, file_path, caption="📄 Here is your movie details file.")
    Title=title
    post_url = await post_to_wordpress(file_path, Title)

# Send the WordPress post link to the user
    await message.reply_text(f"✅ Post published: {post_url}")
    
    
    os.remove(file_path)
    

 
    
# Run the bot
if __name__ == "__main__":
    print("Bot is running...")
    app.run()