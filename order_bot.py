import logging
import json
import os
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
SELLER_CHAT_ID = "455774531"   # Your numeric chat ID (get from @userinfobot)
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
            
            # Extract user info
            user_id = order_data.get('userId', 'Unknown')
            user_name = order_data.get('userName', 'Guest')
            username = order_data.get('username', '')
            first_name = order_data.get('firstName', '')
            last_name = order_data.get('lastName', '')
            items = order_data.get('items', [])
            total = order_data.get('total', '0.00')
            points = order_data.get('points', 0)
            
            # Build customer info using HTML (with <br> not <br/>)
            customer_info = f"👤 <b>Customer:</b> {user_name}<br>"
            if username:
                customer_info += f"🆔 <b>Username:</b> @{username}<br>"
            customer_info += f"🔢 <b>User ID:</b> <code>{user_id}</code><br>"
            if first_name:
                customer_info += f"📛 <b>First Name:</b> {first_name}<br>"
            if last_name:
                customer_info += f"📛 <b>Last Name:</b> {last_name}<br>"
            
            items_text = ""
            for item in items:
                item_name = item.get('name', 'Unknown item')
                item_price = item.get('price', 0)
                items_text += f"  • {item_name} - ${item_price}<br>"
            
            order_text = f"🆕 <b>NEW ORDER!</b><br><br>"
            order_text += customer_info
            order_text += f"<br>📦 <b>Items:</b><br>{items_text}<br>"
            order_text += f"💰 <b>Total:</b> ${total}<br>"
            order_text += f"⭐ <b>Points Earned:</b> {points}<br>"
            order_text += f"🕐 <b>Time:</b> {order_data.get('timestamp', 'N/A')}<br>"
            
            # Send to seller (HTML parse mode)
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