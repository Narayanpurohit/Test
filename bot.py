import os
import re
from imdb import Cinemagoer
from pyrogram import Client, filters

# Initialize IMDbPY
ia = Cinemagoer()

# Initialize the Pyrogram Client
app = Client(
    "imdb_bot",
    api_id=YOUR_API_ID,
    api_hash="YOUR_API_HASH",
    bot_token="YOUR_BOT_TOKEN",
)

def generate_post_from_imdb_link(imdb_url: str, audios: str, category: str, quality: str, media_type: str):
    """Generate a movie post from an IMDb link."""
    try:
        # Extract IMDb ID using regex
        imdb_id_match = re.search(r'tt(\d+)', imdb_url)
        imdb_id = imdb_id_match.group(1) if imdb_id_match else None
        if not imdb_id:
            return "⚠️ Invalid IMDb link!", "Unknown", "Unknown"

        # Fetch movie details
        movie = ia.get_movie(imdb_id)

        # Extract details safely
        title = movie.get('title', 'Unknown Title')
        year = movie.get('year', 'Unknown Year')
        rating = movie.get('rating', 'No Rating')
        genres = ", ".join(movie.get('genres', []))
        plot = movie.get('plot', ['Plot not available'])[0]

        # Extract cast, writers, and directors safely
        cast_list = ", ".join([str(cast) for cast in movie.get('cast', [])[:5]]) or "N/A"
        writers = ", ".join([str(writer) for writer in movie.get('writer', [])[:3]]) or "N/A"
        directors = ", ".join([str(director) for director in movie.get('director', [])[:3]]) or "N/A"

        # Format post using the new template
        post = f"""
<p>{title} ({year}) is now ready for you to Download in {quality} quality, complete with {audios} audio. This {category} hit comes in MKV format. Dive into the world of {genres} with this Movie.</p>

<p>
<span style="color: #339966;"><strong><a style="color: #339966;" href="/">jnmovies </a></strong></span> is your one-stop destination for the latest top-quality Movies, Web Series, and Anime. We provide hassle-free Direct or Google Drive download links for a quick and secure experience. Just click the download button below and follow the simple steps to get your File. Get ready for an unforgettable cinematic experience.
</p>

[imdb style="dark"]{imdb_id}[/imdb]

<h5 style="text-align: center;">
<span style="font-family: arial black, sans-serif; color: #eef425;">
<strong>{title} ({year}) - Movie Download</strong> jnmovies
</span></h5>

<strong>Movie Name:</strong> {title}<br>
<strong>Release Year:</strong> {year}<br>
<strong>Language:</strong> <span style="color: #ff0000;"><strong>{audios}</strong></span><br>
<strong>Genres:</strong> {genres}<br>
<strong>Rating:</strong> {rating}<br>
<strong>Cast:</strong> {cast_list}<br>
<strong>Writer:</strong> {writers}<br>
<strong>Director:</strong> {directors}<br>
<strong>Source:</strong> {quality}<br>

<h4 style="text-align: center;">
<span style="color: #eef425;">Storyline:</span></h4>
<p>{plot}</p>
"""
        return post, title, year
    except Exception as e:
        return f"⚠️ Could not generate post. Error: {e}", "Unknown", "Unknown"

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

        await message.reply_text("Send me the quality:")
        quality = (await client.listen(message.chat.id)).text.strip()

        # Ask for screenshot links
        await message.reply_text("Now send me the screenshot links (each on a new line):")
        screenshots_response = (await client.listen(message.chat.id)).text.strip()
        screenshots = screenshots_response.split("\n")

        if len(screenshots) < 2:
            await message.reply_text("⚠️ Please send at least two screenshot links.")
            return

        # Generate HTML for screenshots
        screenshots_html = '<div class="neoimgs"><div class="screenshots"><ul class="neoscr">\n'
        for link in screenshots:
            screenshots_html += f'<li class="neoss"><img src="{link}" /></li>\n'
        screenshots_html += '</ul></div></div>'

        post, title, year = generate_post_from_imdb_link(text, audios, category, quality, "Movie")

        # Process download links
        await message.reply_text("Send me the download links (`Resolution | Size | Download Link | Stream Link`):")
        download_response = (await client.listen(message.chat.id)).text.strip()
        download_links = download_response.split("\n")

        download_html = ""
        for line in download_links:
            parts = line.split("|")
            if len(parts) == 4:
                resolution, size, dl_link, stream_link = map(str.strip, parts)
                download_html += (
                    f'<h6 style="text-align: center;"><strong>'
                    f'<span style="color: #fff;">{title} ({year}) {audios} {resolution} {quality} [{size}]</span></strong></h6>\n'
                    f'<p style="text-align: center;">'
                    f'<a href="{dl_link}" target="_blank"><button>Download</button></a>\n'
                    f'<a href="{stream_link}" target="_blank"><button>Stream</button></a></p>\n'
                )

        footer = '<hr /><p style="text-align: center;">Keep Visiting and Supporting Us! ❣️</p>'
        html_content = post + "\n\n" + screenshots_html + "\n\n" + download_html + footer

        with open("movie_details.html", "w", encoding="utf-8") as file:
            file.write(html_content)

        await client.send_document(message.chat.id, "movie_details.html", caption="Here is your movie details file.")
        os.remove("movie_details.html")

    else:
        await message.reply_text("⚠️ Please send a valid IMDb link!")