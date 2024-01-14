# bot.py
import logging
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
from config import API_ID, API_HASH, BOT_TOKEN

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the Updater and pass the bot's token
updater = Updater(token=BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hello! I am your Telegram bot. Use /find_replace to perform find and replace.')

def find_replace_in_message(update: Update, context: CallbackContext) -> None:
    try:
        chat_id = update.message.chat_id
        user_message = update.message.text

        # Perform find and replace in the message
        updated_message = user_message.replace("https://m.easysky.in/", "https://techy.veganab.co//")

        context.bot.send_message(chat_id, updated_message)
    except Exception as e:
        context.bot.send_message(chat_id, f"Error during find and replace: {str(e)}")

# Define the command handlers
start_handler = MessageHandler(Filters.command & Filters.private, start)
find_replace_handler = MessageHandler(Filters.text & Filters.private, find_replace_in_message)

# Add the handlers to the dispatcher
dispatcher.add_handler(start_handler)
dispatcher.add_handler(find_replace_handler)

if __name__ == "__main__":
    # Start the Bot
    updater.start_polling()
    updater.idle()
