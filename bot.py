import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import config
import logging
import time

# --- Logging Setup ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Bot Initialization ---
bot = telebot.TeleBot(config.BOT_TOKEN)

# --- Anti-Spam System ---
user_cooldowns = {}
COOLDOWN_TIME = 3 # 3 seconds cooldown for buttons

# --- Helper Functions ---
def check_membership(user_id):
    """Check if the user is a member of all required channels."""
    for channel in config.REQUIRED_CHANNELS:
        try:
            status = bot.get_chat_member(channel['username'], user_id).status
            if status not in ['member', 'administrator', 'creator']:
                return False
        except Exception as e:
            logger.error(f"Error checking membership for {user_id} in {channel['username']}: {e}")
            return False # Assume not joined if there's an error (e.g., bot not admin)
    return True

def generate_join_keyboard():
    """Generates the side-by-side join buttons."""
    markup = InlineKeyboardMarkup()
    buttons = []
    
    # Create buttons for each channel
    for channel in config.REQUIRED_CHANNELS:
        buttons.append(InlineKeyboardButton(text=f"📢 {channel['name']}", url=channel['url']))
    
    # Add buttons side by side (2 buttons per row)
    for i in range(0, len(buttons), 2):
        markup.add(*buttons[i:i+2])
        
    # Add Verify button
    markup.add(InlineKeyboardButton(text="✅ I've Joined", callback_data="check_join"))
    return markup

def generate_success_keyboard():
    """Generates the contact owner button."""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(
        text="👨‍💻 Contact Owner", 
        url=f"https://t.me/{config.OWNER_USERNAME}"
    ))
    return markup

# --- Message Handlers ---
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    logger.info(f"User {user_id} ({first_name}) started the bot.")
    
    if check_membership(user_id):
        bot.send_message(
            message.chat.id,
            f"🎉 Welcome back, *{first_name}*!\n\nYou have already verified your membership. How can I assist you today?",
            parse_mode="Markdown",
            reply_markup=generate_success_keyboard()
        )
    else:
        bot.send_message(
            message.chat.id,
            f"👋 Hello, *{first_name}*!\n\n🔒 *Access Denied*\nTo use this bot, you must join all our official channels below.\n\n👇 Please join and click *I've Joined*.",
            parse_mode="Markdown",
            reply_markup=generate_join_keyboard()
        )

# --- Callback Query Handlers (Button Clicks) ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.from_user.id
    
    # Anti-Spam Check
    current_time = time.time()
    if user_id in user_cooldowns:
        if current_time - user_cooldowns[user_id] < COOLDOWN_TIME:
            bot.answer_callback_query(call.id, "⚠️ Please wait a few seconds before clicking again.", show_alert=False)
            return
    user_cooldowns[user_id] = current_time

    if call.data == "check_join":
        if check_membership(user_id):
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(
                call.message.chat.id,
                "✅ *Verification Successful!*\n\nThank you for joining our channels. You now have full access to the bot.",
                parse_mode="Markdown",
                reply_markup=generate_success_keyboard()
            )
            logger.info(f"User {user_id} successfully verified.")
        else:
            bot.answer_callback_query(
                call.id, 
                "❌ You haven't joined all channels yet! Please join and try again.", 
                show_alert=True
            )

# --- Run the Bot ---
if __name__ == "__main__":
    logger.info("Income_techbot is starting...")
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            logger.error(f"Bot crashed: {e}. Restarting in 5 seconds...")
            time.sleep(5)
