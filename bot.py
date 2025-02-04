from imdb import Cinemagoer
from pyrogram import Client, filters

# Initialize IMDbPY
ia = Cinemagoer()

# Initialize the Pyrogram Client
app = Client(
    "imdb_bot",  # Session name
    api_id=15191874,  # Replace with your API ID
    api_hash="3037d39233c6fad9b80d83bb8a339a07",  # Replace with your API hash
    bot_token="7481801715:AAHo9aeMFR9lK8pwxB5-N_D2zLt5NIVvF2s",  # Replace with your bot token
)

def generate_post_from_imdb_link(imdb_url: str) -> str:
    """Generate a movie post from an IMDb link."""
    try:
        # Extract IMDb ID from the link
        imdb_id = imdb_url.split("/title/")[1].split("/")[0].replace("tt", "")
        # Fetch movie details
        movie = ia.get_movie(imdb_id)
        
        # Generate the post
        title = movie.get('title', 'Unknown Title')
        year = movie.get('year', 'Unknown Year')
        rating = movie.get('rating', 'No Rating')
        genres = ", ".join(movie.get('genres', []))
        plot = movie.get('plot outline', 'Plot not available')

        post = (
            f"🎥 *{title}* ({year})\n"
            f"⭐ *Rating*: {rating}/10\n"
            f"📚 *Genres*: {genres}\n"
            f"📝 *Plot*: {plot}"
        )
        return post
    except Exception as e:
        return f"⚠️ Could not generate post. Error: {e}"

@app.on_message(filters.command("start"))
def start_command(client, message):
    """Handle the /start command."""
    message.reply_text("Hi! Send me an IMDb link, and I'll generate a post for the movie!")

@app.on_message(filters.text)
def handle_message(client, message):
    """Handle incoming IMDb links."""
    text = message.text.strip()

    # Check if the message contains an IMDb link
    if "imdb.com/title/" in text:
        message.reply_text("⏳ Generating post, please wait...")
        post = generate_post_from_imdb_link(text)
        message.reply_text(post)
    else:
        message.reply_text("⚠️ Please send a valid IMDb link!")

# Run the bot
if __name__ == "__main__":
    print("Bot is running...")
    app.run()