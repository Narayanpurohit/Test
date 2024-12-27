from pyrogram import Client, filters
import requests
import os
import time

# Your bot token, API ID, and API Hash
BOT_TOKEN = "YOUR_BOT_TOKEN"
API_ID = "YOUR_API_ID"
API_HASH = "YOUR_API_HASH"

# Directory to store downloaded files temporarily
DOWNLOAD_DIR = "downloads"

# Initialize the bot
app = Client("url_uploader_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# Ensure download directory exists
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

@app.on_message(filters.private & filters.text)
async def handle_url(client, message):
    url = message.text.strip()
    chat_id = message.chat.id

    # Notify the user that the download has started
    try:
        progress_msg = await message.reply_text("🔄 Starting download...")
    except Exception as e:
        print(f"Error sending start message: {e}")

    # Validate URL and download file
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()  # Check if the URL is accessible

        # Extract file name from URL or headers
        file_name = url.split("/")[-1] or "file"
        file_path = os.path.join(DOWNLOAD_DIR, file_name)

        # Download the file with progress updates
        total_size = int(response.headers.get("content-length", 0))
        downloaded_size = 0
        start_time = time.time()

        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
                downloaded_size += len(chunk)

                # Update progress every 5 seconds
                if time.time() - start_time >= 5:
                    speed = downloaded_size / (time.time() - start_time)
                    progress_text = (
                        f"⬇️ Downloading...\n"
                        f"Downloaded: {downloaded_size / 1024:.2f} KB / {total_size / 1024:.2f} KB\n"
                        f"Speed: {speed / 1024:.2f} KB/s"
                    )
                    try:
                        await progress_msg.edit_text(progress_text)
                    except Exception as e:
                        print(f"Error updating download progress: {e}")
                    start_time = time.time()  # Reset start time for next update

        await progress_msg.edit_text("✅ File downloaded successfully. Uploading to Telegram...")
    except requests.exceptions.RequestException as e:
        await progress_msg.edit_text(f"❌ Failed to download the file. Error: {e}")
        return
    except Exception as e:
        await progress_msg.edit_text(f"❌ Unexpected error: {e}")
        return

    # Upload the file to Telegram with progress updates
    try:
        start_time = time.time()
        uploaded_size = 0

        async def progress(current, total):
            nonlocal start_time, uploaded_size
            uploaded_size = current
            if time.time() - start_time >= 5:
                speed = uploaded_size / (time.time() - start_time)
                progress_text = (
                    f"⬆️ Uploading...\n"
                    f"Uploaded: {uploaded_size / 1024:.2f} KB / {total / 1024:.2f} KB\n"
                    f"Speed: {speed / 1024:.2f} KB/s"
                )
                try:
                    await progress_msg.edit_text(progress_text)
                except Exception as e:
                    print(f"Error updating upload progress: {e}")
                start_time = time.time()  # Reset start time for next update

        await client.send_document(chat_id, file_path, progress=progress)
        await progress_msg.edit_text("✅ File uploaded to Telegram successfully.")
    except Exception as e:
        await progress_msg.edit_text(f"❌ Failed to upload the file to Telegram. Error: {e}")
    finally:
        # Cleanup the downloaded file
        if os.path.exists(file_path):
            os.remove(file_path)

# Start the bot
print("Bot is running...")
app.run()