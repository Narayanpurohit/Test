import os
import json
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Replace with your own Client ID and Client Secret from Google Cloud Console
CLIENT_ID = '436657411418-l9efj2619nabmtrm3bhfuilc6b08gm6g.apps.googleusercontent.com'
CLIENT_SECRET = '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'
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Function to authenticate the user and save the token in token.json
def authenticate_user(update: Update, context: CallbackContext):
    if os.path.exists('token.json'):
        update.message.reply_text("You're already authenticated! Use /reset to change account.")
    else:
        flow = Flow.from_client_config(
            {
                "installed": {
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=SCOPES
        )
        auth_url, _ = flow.authorization_url(prompt='consent')
        context.user_data['flow'] = flow
        update.message.reply_text("Please visit the following link to authenticate:\n" + auth_url)

def auth_callback(update: Update, context: CallbackContext):
    code = update.message.text.strip()
    flow = context.user_data.get('flow')
    if not flow:
        update.message.reply_text("Please start with /auth command.")
        return

    flow.fetch_token(code=code)
    credentials = flow.credentials
    with open('token.json', 'w') as token_file:
        token_file.write(credentials.to_json())
    update.message.reply_text("Authentication successful! You can now send files.")

def load_credentials():
    if os.path.exists('token.json'):
        with open('token.json', 'r') as token_file:
            credentials_info = json.load(token_file)
            credentials = google.auth.credentials.Credentials.from_authorized_user_info(credentials_info)
            if credentials.expired:
                credentials.refresh(Request())
                with open('token.json', 'w') as token_file:
                    token_file.write(credentials.to_json())
            return credentials
    return None

def upload_to_drive(file_path, credentials):
    service = build('drive', 'v3', credentials=credentials)
    file_metadata = {'name': os.path.basename(file_path)}
    media = MediaFileUpload(file_path)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')

def handle_file(update: Update, context: CallbackContext):
    credentials = load_credentials()
    if not credentials:
        update.message.reply_text("Please authenticate first with /auth.")
        return

    file = update.message.document or update.message.photo[-1]
    file_id = file.file_id
    file_path = f"downloads/{file.file_name}"

    new_file = context.bot.get_file(file_id)
    new_file.download(file_path)
    update.message.reply_text("File downloaded. Uploading to Google Drive...")

    try:
        file_id = upload_to_drive(file_path, credentials)
        update.message.reply_text(f"File uploaded successfully! File ID: {file_id}")
    except Exception as e:
        update.message.reply_text(f"Failed to upload file: {str(e)}")
    finally:
        os.remove(file_path)

def reset_account(update: Update, context: CallbackContext):
    if os.path.exists('token.json'):
        os.remove('token.json')
    update.message.reply_text("Account reset. Use /auth to authenticate with a new account.")

def main():
    updater = Updater("7481801715:AAEV22RePMaDqd2tyxH0clxtnqd5hDpRuTw", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("auth", authenticate_user))
    dp.add_handler(CommandHandler("authcallback", auth_callback))
    dp.add_handler(CommandHandler("reset", reset_account))

    dp.add_handler(MessageHandler(Filters.document | Filters.photo, handle_file))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()