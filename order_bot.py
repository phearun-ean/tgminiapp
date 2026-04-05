import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Any
from telegram import (
    Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo,
    InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonWebApp
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ContextTypes, CallbackQueryHandler
)
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
SELLER_CHAT_ID = 455774531  # integer (your numeric chat ID)
YOUR_WEB_APP_URL = "https://birdnesttgminiapp.web.app/"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

ORDERS_FILE = "orders.json"

# Structure: order_id -> order_data
def load_orders() -> Dict[str, Any]:
    if os.path.exists(ORDERS_FILE):
        try:
            with open(ORDERS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Failed to load orders: {e}")
            return {}
    return {}

def save_orders(orders: Dict[str, Any]) -> None:
    try:
        with open(ORDERS_FILE, 'w') as f:
            json.dump(orders, f, indent=2)
    except IOError as e:
        logging.error(f"Failed to save orders: {e}")

order_storage = load_orders()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message and set up the Web App button."""
    button = KeyboardButton(
        text="🍽️ Open Order menu",
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

    # Set persistent menu button
    await context.bot.set_chat_menu_button(
        chat_id=update.effective_chat.id,
        menu_button=MenuButtonWebApp(
            text="🍽️ Open Order Menu",
            web_app=WebAppInfo(url=YOUR_WEB_APP_URL)
        )
    )

async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process the order data received from the Web App."""
    message = update.effective_message
    buyer_chat_id = update.effective_chat.id

    if message and message.web_app_data:
        try:
            raw_data = message.web_app_data.data
            order_data = json.loads(raw_data)

            # Extract data with fallbacks
            user_id = order_data.get('userId', 'Unknown')
            user_name = order_data.get('userName', 'Guest')
            username = order_data.get('username', '')
            first_name = order_data.get('firstName', '')
            last_name = order_data.get('lastName', '')
            items = order_data.get('items', [])
            total = order_data.get('total', '0.00')
            points = order_data.get('points', 0)
            timestamp = order_data.get('timestamp', 'N/A')

            # Generate a unique order ID
            order_id = f"ORD_{user_id}_{int(datetime.now().timestamp())}"

            # Store order using order_id as key
            order_storage[order_id] = {
                'chat_id': buyer_chat_id,
                'user_id': user_id,
                'user_name': user_name,
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'timestamp': timestamp,
                'total': total,
                'points': points,
                'items': items
            }
            save_orders(order_storage)

            # Build customer info for seller
            customer_info = f"👤 <b>Customer:</b> {user_name}\n"
            if username:
                customer_info += f"🆔 <b>Username:</b> @{username}\n"
            customer_info += f"🔢 <b>User ID:</b> <code>{user_id}</code>\n"
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
                f"🕐 <b>Time:</b> {timestamp}\n"
                f"🆔 <b>Order ID:</b> <code>{order_id}</code>"
            )

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 Reply to Customer", callback_data=f"reply_{order_id}")],
                [InlineKeyboardButton("✅ Mark as Ready", callback_data=f"ready_{order_id}")]
            ])

            await context.bot.send_message(
                chat_id=SELLER_CHAT_ID,
                text=order_text,
                parse_mode="HTML",
                reply_markup=keyboard
            )

            # Confirm to customer
            await update.message.reply_text(
                f"✅ <b>Order Confirmed, {user_name}!</b>\n\n"
                f"Thank you for your order!\n"
                f"Total: ${total}\n"
                f"You earned {points} loyalty points 🎉\n\n"
                f"We'll notify you when your order is ready.",
                parse_mode="HTML"
            )

            logging.info(f"Order {order_id} from {user_name} (ID: {user_id}): ${total}")

        except Exception as e:
            logging.error(f"Error processing order: {e}", exc_info=True)
            await update.message.reply_text("⚠️ Sorry, there was an error processing your order.")
    else:
        await update.message.reply_text("Click the button below to place an order.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline keyboard callbacks (reply / ready)."""
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("reply_"):
        order_id = data.split("_")[1]
        if order_id in order_storage:
            context.user_data['reply_to_order'] = order_id
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text(
                f"✏️ Type your reply to customer of order {order_id}:\n"
                f"(Send a text message, photo, or any media)"
            )
        else:
            await query.message.reply_text("⚠️ Order data expired or bot restarted. Please ask customer to place a new order.")

    elif data.startswith("ready_"):
        order_id = data.split("_")[1]
        if order_id in order_storage:
            buyer_chat_id = order_storage[order_id]['chat_id']
            user_name = order_storage[order_id]['user_name']
            await context.bot.send_message(
                chat_id=buyer_chat_id,
                text=f"🍽️ <b>Your order is ready for pickup!</b>\n\n"
                     f"Thank you {user_name}! You can come to Bird Nest House to collect your order.\n\n"
                     f"📍 Location: [Your address here]\n"
                     f"⏰ Opening hours: 9AM - 9PM",
                parse_mode="HTML"
            )
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text(f"✅ Sent 'order ready' notification to {user_name} (Order {order_id}).")
            logging.info(f"Notified {user_name} (Order {order_id}) that order is ready.")
        else:
            await query.message.reply_text("⚠️ Order data expired. Cannot send ready notification.")

async def forward_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Forward seller's reply to the customer (text or photo)."""
    if 'reply_to_order' not in context.user_data:
        return

    order_id = context.user_data['reply_to_order']
    if order_id not in order_storage:
        await update.message.reply_text("⚠️ Order session expired. Cannot send message.")
        del context.user_data['reply_to_order']
        return

    buyer_chat_id = order_storage[order_id]['chat_id']
    user_name = order_storage[order_id]['user_name']

    try:
        if update.message.text:
            await context.bot.send_message(
                chat_id=buyer_chat_id,
                text=f"📨 <b>Message from Bird Nest House:</b>\n\n{update.message.text}",
                parse_mode="HTML"
            )
        elif update.message.photo:
            caption = update.message.caption or ""
            await context.bot.send_photo(
                chat_id=buyer_chat_id,
                photo=update.message.photo[-1].file_id,
                caption=f"📨 <b>Message from Bird Nest House:</b>\n\n{caption}",
                parse_mode="HTML"
            )
        elif update.message.sticker:
            await context.bot.send_sticker(
                chat_id=buyer_chat_id,
                sticker=update.message.sticker.file_id
            )
        else:
            await update.message.reply_text("⚠️ Unsupported media type. Send text, photo, or sticker.")
            return

        await update.message.reply_text(f"✅ Message sent to {user_name}!")
        logging.info(f"Reply sent to {user_name} for order {order_id}")
        del context.user_data['reply_to_order']

    except Exception as e:
        logging.error(f"Failed to send reply: {e}")
        await update.message.reply_text("⚠️ Failed to send message. Customer may have blocked the bot or the order chat ID is invalid.")

async def clear_old_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to clear all stored orders (optional)."""
    if update.effective_chat.id == SELLER_CHAT_ID:
        global order_storage
        order_storage = {}
        save_orders(order_storage)
        await update.message.reply_text("🗑️ All order data cleared.")
    else:
        await update.message.reply_text("Unauthorized.")

def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clearorders", clear_old_orders))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_order))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_reply))
    app.add_handler(MessageHandler(filters.PHOTO, forward_reply))
    app.add_handler(MessageHandler(filters.Sticker.ALL, forward_reply))

    print("🤖 Bot is running... Waiting for orders...")
    app.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()