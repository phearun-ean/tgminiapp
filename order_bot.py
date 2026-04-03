import logging
import json
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ========== CONFIGURATION ==========
BOT_TOKEN = "8452975233:AAG-JdJ_0XBspAVj7xKRzbTSdtT0sWz4B-k"        # Your bot token from Step 1
SELLER_CHAT_ID = "455774531"   # Your Chat ID from Step 3
YOUR_WEB_APP_URL = "https://phearun-ean.github.io/tgminiapp/"  # URL of your deployed Mini App
# ===================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message with a button that opens the Mini App."""
    # Create the button that will open your Mini App
    button = KeyboardButton(
        text="🍽️ Open Bird Nest House",
        web_app=WebAppInfo(url=YOUR_WEB_APP_URL)
    )
    # Put the button on the regular keyboard (not inline)
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
    """Process order data sent from the Mini App."""
    message = update.effective_message
    if message and message.web_app_data:
        try:
            order_data = json.loads(message.web_app_data.data)
            customer_name = order_data.get('userName', 'Guest')
            items = order_data.get('items', [])
            total = order_data.get('total', '0.00')
            points = order_data.get('points', 0)
            
            # Build notification for seller
            order_text = f"🆕 *NEW ORDER!*\n\n"
            order_text += f"👤 *Customer:* {customer_name}\n"
            order_text += f"📦 *Items:*\n"
            for item in items:
                order_text += f"  • {item['name']} - ${item['price']}\n"
            order_text += f"\n💰 *Total:* ${total}\n"
            order_text += f"⭐ *Points Earned:* {points}\n"
            order_text += f"🕐 *Time:* {order_data.get('timestamp', 'N/A')}\n"
            
            # Send to seller
            await context.bot.send_message(
                chat_id=SELLER_CHAT_ID,
                text=order_text,
                parse_mode="Markdown"
            )
            
            # Send confirmation back to customer
            await update.message.reply_text(
                f"✅ *Order Confirmed!*\n\n"
                f"Thank you {customer_name}!\n"
                f"Total: ${total}\n"
                f"You earned {points} loyalty points 🎉\n\n"
                f"We'll notify you when your order is ready.",
                parse_mode="Markdown"
            )
            
            logging.info(f"Order processed for {customer_name}: ${total}")
            
        except Exception as e:
            logging.error(f"Error processing order: {e}")
            await update.message.reply_text("⚠️ Sorry, there was an error processing your order.")
    else:
        await update.message.reply_text("Click the button below to place an order.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Command handler for /start
    app.add_handler(CommandHandler("start", start))
    # Handler for web_app_data (orders)
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_order))
    # Optional: handle plain text messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_order))
    
    print("🤖 Bot is running... Waiting for orders...")
    app.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()