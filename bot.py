from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Welcome! Use /findreplace to perform find and replace.')

def find_replace(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    text = context.args[0].lower()  # Assuming the command is /findreplace <text>

    if len(context.args) < 2:
        update.message.reply_text('Usage: /findreplace <find_text> <replace_text>')
        return

    find_text = context.args[0].lower()
    replace_text = context.args[1]

    if update.message.reply_to_message:
        original_text = update.message.reply_to_message.text.lower()
        updated_text = original_text.replace(find_text, replace_text)
        update.message.reply_to_message.reply_text(updated_text)
    else:
        update.message.reply_text('Reply to a message to perform find and replace.')

def main() -> None:
    updater = Updater("6984238382:AAGwQWychtZSdRlnobbQLL9BIxdTidcynrU")

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("findreplace", find_replace, pass_args=True))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
