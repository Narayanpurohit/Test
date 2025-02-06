import os
import re
from imdb import Cinemagoer
from pyrogram import Client, filters
# Initialize IMDbPY
ia = Cinemagoer()

# Initialize the Pyrogram Client
app = Client(
    "imdb_bot",
    api_id=15191874,  # Replace with your API ID
    api_hash="3037d39233c6fad9b80d83bb8a339a07",  # Replace with your API hash
    bot_token="7481801715:AAHo9aeMFR9lK8pwxB5-N_D2zLt5NIVvF2s",  # Replace with your bot token
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
        plot = movie.get('plot', ['Plot not available'])[0]  # Fix plot extraction

        post = (
            f"""<p>{title} (year) is now ready for you to Download in {quality}quality, complete with {audios} audio. This {category} hit comes in MKV format. Dive into the world of {genres} with this Movie.</p>
<p>
<span style="color: #339966;"><strong><a style="color: #339966;" href="/">jnmovies </a></strong></span> is your one-stop destination for the latest top-quality Movies, Web Series, and Anime. We provide hassle-free Direct or Google Drive download links for a quick and secure experience. Just click the download button below and follow the simple steps to get your File. Get ready for an unforgettable cinematic experience</p>

[imdb style="dark"]{movie}[/imdb]
<h5 style="text-align: center;"><span style="font-family: arial black, sans-serif; color: #eef425;"><strong><strong>{title} ({year})- Movie Download </strong> jnmovies </strong></span></h5>

<strong>Movie Name:</strong> {title}
<strong>Release Year:</strong> {year}
<strong>Language:</strong> <span style="color: #ff0000;"><strong>{audio} </strong></span>
<strong>Genres:</strong> {genres}
<strong>Rating:</strong> {rating}
<strong>Cast:</strong> {cast_list}
<strong>Writer:</strong> {writers}
<strong>Director:</strong> {directors}
<strong>Source:</strong> {quality}
<strong>Subtitle:</strong> YES / English
<strong>Format:</strong> MKV


<h4 style="text-align: center;"><span style="color: #eef425;">Storyline:</span></h4><p>
{plot}</p>"""
            
        )
        return post, title, year  # Return title and year for use in download links
    except Exception as e:
        return f"⚠️ Could not generate post. Error: {e}", "Unknown", "Unknown"

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

        # Ask for screenshot links
        await message.reply_text("Now send me the screenshot links (each on a new line):")
        screenshots_response = (await client.listen(message.chat.id)).text.strip()

        
        # Generate IMDb Post
        
        # Ask for download links
        await message.reply_text(
            "Now send me the download links in this format:\n"
            "`Resolution | Size | Download Link | Stream Link`\n"
            "You can send multiple lines for multiple links."
        )
        download_response = (await client.listen(message.chat.id)).text.strip()
        
        m=await message.reply_sticker("CAACAgQAAxkBAAEKeqNlIpmeUoOEsEWOWEiPxPi3hH5q-QACbg8AAuHqsVDaMQeY6CcRojAE") 

        screenshots = screenshots_response.split("\n")
        if len(screenshots) < 2:
            await m.delete()
            await message.reply_text("⚠️ Please send at least two screenshot links.")
            
            return
        
        # Generate HTML for screenshots
        screenshots_html = '<div class="neoimgs"><div class="screenshots"><ul class="neoscr">\n'
        for link in screenshots[1:]:
            screenshots_html += f'<li class="neoss"><img src="{link}" /></li>\n'
        screenshots_html += '</ul></div></div>'

        post, title, year = generate_post_from_imdb_link(text, audios, category, quality, media_type)

        # Process download links
        download_links = download_response.split("\n")
        download_html = ""

        for line in download_links:
            parts = line.split("|")
            if len(parts) == 4:
                resolution = parts[0].strip()
                size = parts[1].strip()
                dl_link = parts[2].strip()
                stream_link = parts[3].strip()

                download_html += (
                    f'<h6 style="text-align: center;"><strong>'
                    f'<span style="color: #fff;">{title} ({year}) {audios} {resolution} {quality} [{size}]</span></strong></h6>\n'
                    f'<p style="text-align: center;">'
                    f'<a href="{dl_link}" target="_blank" rel="noopener">'
                    f'<button class="dwd-button"> <i class="fas fa-download"></i> Download Link</button></a>\n'
                    f'<a href="{stream_link}" target="_blank" rel="noopener">'
                    f'<button class="dwd-button"> <i class="fas fa-play"></i> Stream Link</button></a></p>\n'
                )
            else:
                await message.reply_text(f"⚠️ Invalid format in: `{line}`. Skipping this line.")
                await m.delete()

        # Final HTML content
        html_content = post + "\n\n" + screenshots_html + "\n\n" + download_html  

        # Save to a .html file
        file_path = "movie_details.html"
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(html_content)

        # Send the file
        
        await client.send_document(
            chat_id=message.chat.id,
            document=file_path,
            caption="Here is your movie details file."
        )
        
        await m.delete()

        # Delete the file after sending
        
        os.remove(file_path)

    else:
        await message.reply_text("⚠️ Please send a valid IMDb link!")

# Run the bot
if __name__ == "__main__":
    print("Bot is running...")
    app.run()