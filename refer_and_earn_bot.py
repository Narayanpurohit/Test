from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
TOKEN = 'YOUR_BOT_TOKEN'

# Dictionary to store user referrals
referral_dict = {}

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Welcome to the Refer and Earn Bot! Share your referral link to earn rewards.")

def refer(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    referral_link = f"https://t.me/YourBotUsername?start={user_id}"
    update.message.reply_text(f"Your referral link: {referral_link}")

def process_referral(update: Update, context: CallbackContext) -> None:
    referred_user_id = update.message.from_user.id
    referrer_user_id = update.message.text.split('/start=')[-1]

    if referrer_user_id.isnumeric():
        referrer_user_id = int(referrer_user_id)
        referral_dict[referred_user_id] = referrer_user_id
        update.message.reply_text("Referral successful! The referrer will earn rewards.")

# Set up the bot handlers
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("refer", refer))
dispatcher.add_handler(MessageHandler(Filters.regex(r'/start='), process_referral))

# Start the bot
updater.start_polling()
updater.idle()
