WORDPRESS_URL = "https://yourwebsite.com/wp-json/wp/v2/posts"
WORDPRESS_USERNAME = "your-username"
WORDPRESS_APP_PASSWORD = "your-application-password"

# config.py

# 🔹 Bot Credentials
API_ID = 15191874  # Replace with your API ID
API_HASH = "3037d39233c6fad9b80d83bb8a339a07"  # Replace with your API hash
BOT_TOKEN = "6677023637:AAES7_yErqBDZY7wQP1EOyIGhpAN1d9fY5o"  # Replace with your bot token

# 🔹 MongoDB Connection
MONGO_URI = "mongodb+srv://jnbots76:jacIjUcT5DBeBCdM@cluster0.tsrup.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # Change if using cloud MongoDB
DB_NAME = "telegram_bot"
COLLECTION_NAME = "users"

# 🔹 Default Templates
DEFAULT_POST_TEMPLATE = """
<p>{title} ({year}) is now ready for you to Download in {quality} quality, complete with {audios} audios. This {category} hit comes in MKV format. Dive into the world of {genres} with this Movie.</p>

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
<p>{plot}</p>"""
DEFAULT_FOOTER_TEMPLATE = """<hr /><p style="text-align: center;">Keep Visiting and Supporting Us! ❣️</p>"""