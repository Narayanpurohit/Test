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
from config import API_ID, API_HASH, BOT_TOKEN, MONGO_URI, DB_NAME, COLLECTION_NAME, DEFAULT_POST_TEMPLATE, DEFAULT_FOOTER_TEMPLATE,DEFAULT_WORDPRESS_URL,DEFAULT_WORDPRESS_USERNAME,DEFAULT_WORDPRESS_APP_PASSWORD,DEFAULT_SS1,DEFAULT_SS2,DEFAULT_SS3,DEFAULT_DL1,DEFAULT_DL2

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

def download_imdb_poster(poster_url, movie_title):
    """Downloads and saves the IMDb poster."""
    
    if not poster_url:
        return None

    ext = poster_url.split(".")[-1].split("?")[0]
    file_name = f"{movie_title}.{ext}"
    file_path = os.path.join("/tmp", file_name)

    response = requests.get(poster_url, stream=True)
    if response.status_code == 200:
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        return file_path
    return None


async def post_to_wordpress(file_path, title,user_id):
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
    
    
    user = await get_user_data(user_id)
    WORDPRESS_USERNAME = user["wp_username"]
    WORDPRESS_URL = user["wp_url"]
    WORDPRESS_APP_PASSWORD = user["wp_passwd"]
    
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
            "ss1":DEFAULT_SS1,
            "ss2":DEFAULT_SS2,
            "ss3":DEFAULT_SS3,
            "dl1":DEFAULT_DL1,
            "dl2":DEFAULT_DL2,
            "auto_post":False,
            "wp_url": DEFAULT_WORDPRESS_URL,
            "wp_username": DEFAULT_WORDPRESS_USERNAME,
            "wp_passwd": DEFAULT_WORDPRESS_APP_PASSWORD,
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
    await message.reply_text("hello! Use /newpost to generate a movie post!")


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

    
    await message.reply_text(" Send me the **Poster Url** :")
    poster_url = (await client.listen(message.chat.id)).text.strip()

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
    await generate_post(client, message, user_id, imdb_link, audios, category, quality, type, screenshots, download_links,poster_url)


async def generate_post(client, message, user_id, imdb_url, audios, category, quality, type, screenshots, download_links,poster_url):
    """Generate a post using all collected details."""

    # Get user templates
    user = await get_user_data(user_id)
    post_template = user["post_template"]
    ss1 = user["ss1"]
    ss2 = user["ss2"]
    ss3 = user["ss3"]
    dl1 = user["dl1"]
    dl2 = user["dl2"]
    footer_template = user["footer_template"]

    print(imdb_url)
    # Extract IMDb ID
    imdb_id_match = re.search(r'tt(\d+)', imdb_url)
    imdb_id = imdb_id_match.group(1) if imdb_id_match else None
    if not imdb_id:
        await message.reply_text("⚠️ Invalid IMDb link!")
        return

    # Fetch movie details
    movie = ia.get_movie(imdb_id)
    title = movie.get('title', 'Unknown Title')
    rating = movie.get('rating', 'No Rating')
    year = movie.get('year', 'Unknown Year')
    genres = ", ".join(movie.get('genres', []))
    plot = movie.get('plot', ['Plot not available'])[0]
    cast_list = ", ".join([str(cast) for cast in movie.get('cast', [])[:5]]) or "N/A"
    writers = ", ".join([str(writer) for writer in movie.get('writer', [])[:3]]) or "N/A"
    directors = ", ".join([str(director) for director in movie.get('director', [])[:3]]) or "N/A"

    
    
    print(poster_url)
        
    # Generate Screenshot Links in HTML
    #ss2=ss2.format(link=link )
    screenshots_html = ss1
    for link in screenshots:
        screenshots_html += ss2.format(link=link )
    screenshots_html += ss3

    # Generate Download Buttons
    download_html = ""
    for line in download_links:
        parts = line.split("|")
        if len(parts) == 4:
            resolution, size, dl_link, stream_link = map(str.strip, parts)
            download_html += dl1.format(resolution=resolution,size=size,dl_link=dl_link,stream_link=stream_link,title=title,year=year
)
            download_html += dl2.format(resolution=resolution,size=size,dl_link=dl_link,stream_link=stream_link,title=title,year=year)

    # Fill the template
    post = post_template.format(poster_url=poster_url,title=title, year=year, genres=genres, plot=plot, quality=quality,audios=audios, category=category,type=type,imdb_id=imdb_id,directors =directors,writers=writers,cast_list=cast_list,rating=rating )
    
    
    
    
    
    
    
    html_content = post + "\n\n" + screenshots_html + "\n\n" + download_html + footer_template

    
    
    
    # Save to a .html file
    file_path = "movie_details.html"
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(html_content)
    

    await client.send_document(message.chat.id, file_path, caption="📄 Here is your movie details file.")
    
    Title=title+"{year}"
    user_id=message.chat.id
    post_url = await post_to_wordpress(file_path, Title,user_id)

# Send the WordPress post link to the user
    await message.reply_text(f"✅ Post published: {post_url}")
    
    
    os.remove(file_path)
    
@app.on_message(filters.command("settings"))
async def settings_command(client, message):
    """Send settings options with an inline button."""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Post Template", callback_data="post_template")]
    ])
    await message.reply_text("⚙️ **Settings**\nChoose an option:", reply_markup=keyboard)


@app.on_callback_query()
async def callback_handler(client, callback_query):
    """Handle different callback queries separately."""
    data = callback_query.data

    if data == "post_template":
        await send_post_template(client, callback_query)
    elif data == "change_template":
        await change_post_template(client, callback_query)


async def send_post_template(client, callback_query):
    """Send the current post template as a .txt file with an option to change it."""
    user_id = callback_query.from_user.id
    user = await get_user_data(user_id)
    post_template = user["post_template"]

    file_path = "post_template.txt"
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(post_template)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Change Template", callback_data="change_template")]
    ])
    
    await client.send_document(
        chat_id=callback_query.message.chat.id,
        document=file_path,
        caption="📄 Here is your current post template.",
        reply_markup=keyboard
    )
    os.remove(file_path)


async def change_post_template(client, callback_query):
    """Ask user to send a new post template."""
    user_id = callback_query.from_user.id
    await client.send_message(user_id, "✏️ Send me the new **post template** as text.")

    response = (await client.listen(user_id)).text.strip()

    await users_collection.update_one(
        {"user_id": user_id}, {"$set": {"post_template": response}}
    )
    
    await client.send_message(user_id, "✅ **Post template updated successfully!**")
    


@app.on_message(filters.command("delete") & filters.private)
async def delete_user(client, message):
    """Delete a specific user from MongoDB using /delete user_id."""
    try:
        # Get the user ID from the command
        command_parts = message.text.split()
        if len(command_parts) != 2 or not command_parts[1].isdigit():
            await message.reply_text("❌ Invalid format! Use:\n`/delete <user_id>`")
            return

        user_id = int(command_parts[1])  # Convert user_id to integer

        # Delete user from MongoDB
        result = await users_collection.delete_one({"user_id": user_id})

        if result.deleted_count > 0:
            await message.reply_text(f"✅ User `{user_id}` has been deleted from the database.")
        else:
            await message.reply_text(f"❌ No data found for user `{user_id}`.")

    except Exception as e:
        await message.reply_text(f"❌ Error: `{str(e)}`")


# Run the bot
if __name__ == "__main__":
    print("Bot is running...")
    app.run()