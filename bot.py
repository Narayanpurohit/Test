import os
import re
from imdb import Cinemagoer
from pyrogram import Client, filters

# Initialize IMDbPY
ia = Cinemagoer()

# Initialize the Pyrogram Client
app = Client(
    "imdb_bot",
    api_id=YOUR_API_ID,  # Replace with your API ID
    api_hash="YOUR_API_HASH",  # Replace with your API hash
    bot_token="YOUR_BOT_TOKEN",  # Replace with your bot token
)

def generate_post_from_imdb_link(imdb_url: str, audios: str, category: str, quality: str, media_type: str) -> str:
    """Generate a movie post from an IMDb link."""
    try:
        # Extract IMDb ID using regex
        imdb_id_match = re.search(r'tt(\d+)', imdb_url)
        imdb_id = imdb_id_match.group(1) if imdb_id_match else None
        if not imdb_id:
            return "⚠️ Invalid IMDb link!"

        # Fetch movie details
        movie = ia.get_movie(imdb_id)
        
        # Generate the post
        title = movie.get('title', 'Unknown Title')
        year = movie.get('year', 'Unknown Year')
        rating = movie.get('rating', 'No Rating')
        genres = ", ".join(movie.get('genres', []))
        plot = movie.get('plot outline', 'Plot not available')

        post = (
            f"<p>🎥 *{title}* ({year})</p>\n"
            f"⭐ *Rating*: {rating}/10\n"
            f"🎧 *Languages*: {audios}\n"
            f"📚 *Genres*: {genres}\n"
            f"📝 *Category*: {category}\n"
            f"📝 *Quality*: {quality}\n"
            f"📝 *Type*: {media_type}\n"
            f"📝 *Plot*: {plot}"
        )
        return post
    except Exception as e:
        return f"⚠️ Could not generate post. Error: {e}"

@app.on_message(filters.command("start"))
async def start_command(client, message):
    """Handle the /start command."""
    await message.reply_text("Hi! Send me an IMDb link, and I'll generate a post for the movie!")

@app.on_message(filters.text)
async def handle_message(client, message):
    """Handle incoming IMDb links."""
    text = message.text.strip()

    if "imdb.com/title/" in text:
        # Ask user for inputs
        await message.reply_text("Send me the audio languages (e.g., Hindi, English, Tamil):")
        audios = (await client.listen(message.chat.id)).text.strip()

        await message.reply_text("Send me the category (e.g., Hollywood, Bollywood, Anime, etc.):")
        category = (await client.listen(message.chat.id)).text.strip()

        await message.reply_text(
            "Send me the quality (Choose from below):\n"
            "```CAM, HDCAM, TS, HDTS, WEBRip, WEB-DL, HDTV, PDTV, DVDScr, DVDRip, BDRip, BRRip, REMUX, HDRip, 4K UHD BluRay Rip, Lossless```"
        )
        quality = (await client.listen(message.chat.id)).text.strip()

        await message.reply_text("Send me the type (e.g., Movie, Web Series, etc.):")
        media_type = (await client.listen(message.chat.id)).text.strip()

        # Ask for links
        await message.reply_text("Now send me the links (each on a new line):")
        links_response = (await client.listen(message.chat.id)).text.strip()

        links = links_response.split("\n")
        if len(links) < 2:
            await message.reply_text("⚠️ Please send at least two links.")
            return
        
        # Generate HTML download buttons
        html_template = '<p style="text-align: center;">\n'
        for link in links[1:]:
            html_template += (
                f'<a href="{link}" target="_blank" rel="noopener">'
                f'<button class="dwd-button"> <i class="fas fa-download"></i> Download Link</button></a>\n'
            )
        html_template += '</p>'

        # Generate IMDb Post
        post = generate_post_from_imdb_link(text, audios, category, quality, media_type)
        html_content = html_template + "\n\n" + post  # Combine HTML + Post

        # Save to a .txt file
        file_path = "download_links.txt"
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(html_content)

        # Send the file
        await client.send_document(
            chat_id=message.chat.id,
            document=file_path,
            caption="Here is your download links file."
        )

        # Delete the file after sending
        os.remove(file_path)

    else:
        await message.reply_text("⚠️ Please send a valid IMDb link!")

# Run the bot
if __name__ == "__main__":
    print("Bot is running...")
    app.run()