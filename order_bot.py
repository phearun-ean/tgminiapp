import logging
import json
import os
import html
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
SELLER_CHAT_ID = "455774531"   # Your numeric chat ID
YOUR_WEB_APP_URL = "https://phearun-ean.github.io/tgminiapp/"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

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
    
    if message and message.web_app_data:
        try:
            raw_data = message.web_app_data.data
            order_data = json.loads(raw_data)
            
            # Extract user info with safe defaults
            user_id = html.escape(str(order_data.get('userId', 'Unknown')))
            user_name = html.escape(order_data.get('userName', 'Guest'))
            username = html.escape(order_data.get('username', ''))
            first_name = html.escape(order_data.get('firstName', ''))
            last_name = html.escape(order_data.get('lastName', ''))
            items = order_data.get('items', [])
            total = html.escape(order_data.get('total', '0.00'))
            points = html.escape(str(order_data.get('points', 0)))
            timestamp = html.escape(order_data.get('timestamp', 'N/A'))
            
            # Build customer info using newlines (no HTML tags needed for layout)
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
                item_name = html.escape(item.get('name', 'Unknown item'))
                item_price = html.escape(str(item.get('price', 0)))
                items_text += f"  • {item_name} - ${item_price}\n"
            
            order_text = (
                f"🆕 <b>NEW ORDER!</b>\n\n"
                f"{customer_info}\n"
                f"📦 <b>Items:</b>\n{items_text}\n"
                f"💰 <b>Total:</b> ${total}\n"
                f"⭐ <b>Points Earned:</b> {points}\n"
                f"🕐 <b>Time:</b> {timestamp}"
            )
            
            # Send to seller
            await context.bot.send_message(
                chat_id=SELLER_CHAT_ID,
                text=order_text,
                parse_mode="HTML"
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
            
            logging.info(f"Order from {user_name} (ID: {user_id}): ${total}")
            
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error: {e}")
            await update.message.reply_text("⚠️ Invalid order data format.")
        except Exception as e:
            logging.error(f"Error processing order: {e}", exc_info=True)
            await update.message.reply_text("⚠️ Sorry, there was an error processing your order.")
    else:
        await update.message.reply_text("Click the button below to place an order.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_order))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_order))
    
    print("🤖 Bot is running... Waiting for orders...")
    app.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()