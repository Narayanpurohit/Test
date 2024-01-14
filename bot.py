# bot.py
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the token for your Telegram bot
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# Initialize the Updater and pass the bot's token
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hello! I am your Telegram bot. Use /find_replace to perform find and replace.')

def find_replace(update: Update, context: CallbackContext) -> None:
    try:
        file_path = context.args[0]
        find_text = context.args[1]
        replace_text = context.args[2]

        with open(file_path, 'r') as file:
            content = file.read()

        updated_content = content.replace(find_text, replace_text)

        with open(file_path, 'w') as file:
            file.write(updated_content)

        update.message.reply_text(f"Find and replace in {file_path} completed successfully.")
    except Exception as e:
        update.message.reply_text(f"Error during find and replace: {str(e)}")

# Define the command handlers
start_handler = CommandHandler('start', start)
find_replace_handler = CommandHandler('find_replace', find_replace)

# Add the handlers to the dispatcher
dispatcher.add_handler(start_handler)
dispatcher.add_handler(find_replace_handler)

if __name__ == "__main__":
    # Start the Bot
    updater.start_polling()
    updater.idle()
