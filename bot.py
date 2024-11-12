import os
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackContext, Updater
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import config

def start(update: Update, context: CallbackContext):
    """Sends a welcome message when the bot is started."""
    update.message.reply_text(
        "Welcome to your personal Google Drive bot! Use /auth to authenticate your Google Drive account. "
        "After authentication, you can send any file to upload it to your Google Drive."
    )
    print("Bot started and ready to receive commands.")

def authenticate_user(update: Update, context: CallbackContext):
    """Starts the Google authentication flow."""
    flow = Flow.from_client_config(
        {
            "installed": {
                "client_id": config.CLIENT_ID,
                "client_secret": config.CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=['https://www.googleapis.com/auth/drive.file']
    )

    # Set the redirect URI explicitly for desktop app
    flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'

    # Generate the authorization URL
    auth_url, _ = flow.authorization_url(prompt='consent')
    context.user_data['flow'] = flow
    update.message.reply_text("Please visit the following link to authenticate:\n" + auth_url)

def handle_auth_code(update: Update, context: CallbackContext):
    """Handles the authorization code provided by the user and completes the Google authentication."""
    auth_code = update.message.text
    flow = context.user_data.get('flow')

    if not flow:
        update.message.reply_text("Please use /auth to start the authentication process.")
        return

    # Exchange the authorization code for credentials
    flow.fetch_token(code=auth_code)
    credentials = flow.credentials
    context.user_data['credentials'] = credentials

    update.message.reply_text("Authentication successful! You can now upload files.")

def upload_file(update: Update, context: CallbackContext):
    """Uploads the received file to Google Drive."""
    credentials = context.user_data.get('credentials')

    if not credentials:
        update.message.reply_text("Please authenticate first using /auth.")
        return

    # Download the file sent by the user
    file = update.message.document.get_file()
    file_path = file.download()

    # Initialize Google Drive API client
    drive_service = build('drive', 'v3', credentials=credentials)

    # Upload the file to Google Drive
    file_metadata = {'name': update.message.document.file_name}
    media = MediaFileUpload(file_path, mimetype=update.message.document.mime_type)
    drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    # Confirm the file upload
    update.message.reply_text(f"File '{update.message.document.file_name}' has been uploaded to Google Drive.")

    # Clean up the downloaded file
    os.remove(file_path)

def main():
    """Main function to start the bot and add all handlers."""
    updater = Updater(config.BOT_TOKEN)
    dp = updater.dispatcher

    # Add handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("auth", authenticate_user))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_auth_code))  # To handle the auth code
    dp.add_handler(MessageHandler(Filters.document, upload_file))  # To handle file uploads

    # Start polling and keep the bot running
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()