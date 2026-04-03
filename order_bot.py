import logging
import json
import os
from datetime import datetime
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
SELLER_CHAT_ID = "455774531"
YOUR_WEB_APP_URL = "https://phearun-ean.github.io/tgminiapp/"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

ORDERS_FILE = "orders.json"

def load_orders():
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_orders(orders):
    with open(ORDERS_FILE, 'w') as f:
        json.dump(orders, f, indent=2)

# Load existing orders
order_storage = load_orders()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    button = KeyboardButton(
        text="🍽️ Open Bird Nest House",
        web_app=WebAppInfo(url=YOUR_WEB_APP_URL)
    )
    reply_markup = ReplyKeyboardMarkup(
        keyboard=[[button]],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    await update.message.reply_text(
        "Welcome to Bird Nest House! 🥚\nClick the button below to place your order:",
        reply_markup=reply_markup
    )

async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    buyer_chat_id = str(update.effective_chat.id)  # Use chat_id as primary key
    
    if message and message.web_app_data:
        try:
            raw_data = message.web_app_data.data
            order_data = json.loads(raw_data)
            
            user_id = order_data.get('userId', 'Unknown')
            user_name = order_data.get('userName', 'Guest')
            username = order_data.get('username', '')
            first_name = order_data.get('firstName', '')
            last_name = order_data.get('lastName', '')
            items = order_data.get('items', [])
            total = order_data.get('total', '0.00')
            points = order_data.get('points', 0)
            timestamp = order_data.get('timestamp', 'N/A')
            
            # Store using buyer_chat_id (more reliable)
            order_storage[buyer_chat_id] = {
                'user_id': user_id,
                'user_name': user_name,
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'chat_id': buyer_chat_id,
                'order_id': f"ORD_{buyer_chat_id}_{int(datetime.now().timestamp())}",
                'items': items,
                'total': total,
                'points': points,
                'timestamp': timestamp
            }
            save_orders(order_storage)
            
            # Build customer info
            customer_info = f"👤 <b>Customer:</b> {user_name}\n"
            if username:
                customer_info += f"🆔 <b>Username:</b> @{username}\n"
            customer_info += f"🔢 <b>Chat ID:</b> <code>{buyer_chat_id}</code>\n"
            if first_name:
                customer_info += f"📛 <b>First Name:</b> {first_name}\n"
            if last_name:
                customer_info += f"📛 <b>Last Name:</b> {last_name}\n"
            
            items_text = ""
            for item in items:
                item_name = item.get('name', 'Unknown item')
                item_price = item.get('price', 0)
                items_text += f"  • {item_name} - ${item_price}\n"
            
            order_text = (
                f"🆕 <b>NEW ORDER!</b>\n\n"
                f"{customer_info}\n"
                f"📦 <b>Items:</b>\n{items_text}\n"
                f"💰 <b>Total:</b> ${total}\n"
                f"⭐ <b>Points Earned:</b> {points}\n"
                f"🕐 <b>Time:</b> {timestamp}"
            )
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 Reply to Customer", callback_data=f"reply_{buyer_chat_id}")],
                [InlineKeyboardButton("✅ Mark as Ready", callback_data=f"ready_{buyer_chat_id}")]
            ])
            
            await context.bot.send_message(
                chat_id=SELLER_CHAT_ID,
                text=order_text,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            
            await update.message.reply_text(
                f"✅ <b>Order Confirmed, {user_name}!</b>\n\n"
                f"Thank you for your order!\n"
                f"Total: ${total}\n"
                f"You earned {points} loyalty points 🎉\n\n"
                f"We'll notify you when your order is ready.",
                parse_mode="HTML"
            )
            
            logging.info(f"Order from {user_name} (Chat ID: {buyer_chat_id}): ${total}")
            
        except Exception as e:
            logging.error(f"Error processing order: {e}", exc_info=True)
            await update.message.reply_text("⚠️ Sorry, there was an error processing your order.")
    else:
        await update.message.reply_text("Click the button below to place an order.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    # Extract the chat_id (now stored as string)
    if data.startswith("reply_"):
        chat_id = data.split("_", 1)[1]
        if chat_id in order_storage:
            context.user_data['reply_to'] = chat_id
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text(
                f"✏️ Type your reply to {order_storage[chat_id]['user_name']}:\n"
                f"(Send a text message, photo, or any media)"
            )
        else:
            logging.warning(f"Reply failed: chat_id {chat_id} not found in storage. Available keys: {list(order_storage.keys())}")
            await query.message.reply_text("⚠️ Customer info expired. Cannot reply. The customer may need to place a new order.")
    
    elif data.startswith("ready_"):
        chat_id = data.split("_", 1)[1]
        if chat_id in order_storage:
            buyer_chat_id = int(chat_id)  # chat_id stored as string, but send_message expects int
            user_name = order_storage[chat_id]['user_name']
            await context.bot.send_message(
                chat_id=buyer_chat_id,
                text=f"🍽️ <b>Your order is ready for pickup!</b>\n\n"
                     f"Thank you {user_name}! You can come to Bird Nest House to collect your order.\n\n"
                     f"📍 Location: [Your address here]\n"
                     f"⏰ Opening hours: 9AM - 9PM",
                parse_mode="HTML"
            )
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text(f"✅ Sent 'order ready' notification to {user_name}.")
            logging.info(f"Notified {user_name} (Chat ID: {chat_id}) that order is ready.")
        else:
            logging.warning(f"Ready failed: chat_id {chat_id} not found in storage.")
            await query.message.reply_text("⚠️ Customer info expired. Cannot send ready notification.")

async def forward_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'reply_to' not in context.user_data:
        return
    
    chat_id = context.user_data['reply_to']
    if chat_id not in order_storage:
        await update.message.reply_text("⚠️ Customer session expired. Cannot send message.")
        del context.user_data['reply_to']
        return
    
    buyer_chat_id = int(chat_id)
    user_name = order_storage[chat_id]['user_name']
    
    try:
        if update.message.text:
            await context.bot.send_message(
                chat_id=buyer_chat_id,
                text=f"📨 <b>Message from Bird Nest House:</b>\n\n{update.message.text}",
                parse_mode="HTML"
            )
        elif update.message.photo:
            await context.bot.send_photo(
                chat_id=buyer_chat_id,
                photo=update.message.photo[-1].file_id,
                caption=f"📨 <b>Message from Bird Nest House:</b>\n\n{update.message.caption or ''}",
                parse_mode="HTML"
            )
        elif update.message.sticker:
            await context.bot.send_sticker(
                chat_id=buyer_chat_id,
                sticker=update.message.sticker.file_id
            )
        else:
            await update.message.reply_text("⚠️ Unsupported media type. Send text or photo.")
            return
        
        await update.message.reply_text(f"✅ Message sent to {user_name}!")
        logging.info(f"Reply sent to {user_name} (Chat ID: {chat_id})")
        del context.user_data['reply_to']
        
    except Exception as e:
        logging.error(f"Failed to send reply: {e}")
        await update.message.reply_text("⚠️ Failed to send message. Customer may have blocked the bot.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_order))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_reply))
    app.add_handler(MessageHandler(filters.PHOTO, forward_reply))
    app.add_handler(MessageHandler(filters.Sticker.ALL, forward_reply))
    
    print("🤖 Bot is running... Waiting for orders...")
    app.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()