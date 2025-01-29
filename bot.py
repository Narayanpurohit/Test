from imdb import Cinemagoer
from pyrogram import Client, filters
from pyrogram.types import Message

# Initialize IMDbPY
ia = Cinemagoer()

# Your bot token, API ID, and API Hash
BOT_TOKEN = "6677023637:AAFWgnwC7FVHV57mGlMRBusZqNFnV6nVktM"
API_ID = "15191874"
API_HASH = "3037d39233c6fad9b80d83bb8a339a07"

# Initialize the Pyrogram Client
app = Client(
    "imdb_bot",
    api_id=int(API_ID),
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

# Dictionary to track users and their screenshot submissions
pending_screenshots = {}

def generate_post_from_imdb_link(imdb_url: str, screenshots: list) -> str:
    """Generate a movie post from an IMDb link and screenshots."""
    try:
        imdb_id = imdb_url.split("/title/")[1].split("/")[0].replace("tt", "")
        movie = ia.get_movie(imdb_id)

        title = movie.get('title', 'Unknown Title')
        year = movie.get('year', 'Unknown Year')
        rating = movie.get('rating', 'No Rating')
        genres = ", ".join(movie.get('genres', []))
        plot = movie.get('plot outline', 'Plot not available')

        post = (
            f"🎥 *{title}* ({year})\n"
            f"⭐ *Rating*: {rating}/10\n"
            f"📚 *Genres*: {genres}\n"
            f"📝 *Plot*: {plot}\n\n"
        )

        if screenshots:
            post += '<div class="neoimgs">\n<div class="screenshots">\n<ul class="neoscr">\n'
            for url in screenshots:
                post += f'  <li class="neoss"><img src="{url}" /></li>\n'
            post += '</ul>\n</div>\n</div>'

        return post
    except Exception as e:
        return f"⚠️ Could not generate post. Error: {e}"

@app.on_message(filters.command("start"))
def start_command(client, message: Message):
    """Handle the /start command."""
    message.reply_text("Hi! Send me an IMDb link, and I'll generate a post for the movie!")

@app.on_message(filters.text)
def handle_message(client, message: Message):
    """Handle IMDb links and screenshot collection."""
    user_id = message.from_user.id
    text = message.text.strip()

    # If user is sending screenshot URLs
    if user_id in pending_screenshots:
        if text.lower() == "done":
            # User finished sending screenshots, generate the final post
            imdb_url, screenshots = pending_screenshots.pop(user_id)
            post = generate_post_from_imdb_link(imdb_url, screenshots)
            message.reply_text(post, disable_web_page_preview=True)
        else:
            # Store each screenshot URL line by line
            pending_screenshots[user_id][1].append(text)
            message.reply_text("✅ Screenshot added! Send another or type *done* when finished.")

    # If user sends an IMDb link
    elif "imdb.com/title/" in text:
        pending_screenshots[user_id] = [text, []]  # Store IMDb URL with an empty list for screenshots
        message.reply_text("📸 Send screenshot URLs (one per line). Type *done* when finished:")

    else:
        message.reply_text("⚠️ Please send a valid IMDb link!")

# Run the bot
if __name__ == "__main__":
    print("Bot is running...")
    app.run()