import logging
import json
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# ========== CONFIGURATION ==========
BOT_TOKEN = "8452975233:AAG-JdJ_0XBspAVj7xKRzbTSdtT0sWz4B-k"        # Your bot token from Step 1
SELLER_CHAT_ID = "455774531"   # Your Chat ID from Step 3
# ===================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process order data from Mini App and forward to seller."""
    message = update.effective_message
    
    # Check if message contains web_app_data (order from Mini App)
    if message and message.web_app_data:
        try:
            order_data = json.loads(message.web_app_data.data)
            customer_name = order_data.get('userName', 'Guest')
            items = order_data.get('items', [])
            total = order_data.get('total', '0.00')
            points = order_data.get('points', 0)
            
            # Build formatted message for seller
            order_text = f"🆕 *NEW ORDER RECEIVED!*\n\n"
            order_text += f"👤 *Customer:* {customer_name}\n"
            order_text += f"📦 *Items:*\n"
            for item in items:
                order_text += f"  • {item['name']} - ${item['price']}\n"
            order_text += f"\n💰 *Total:* ${total}\n"
            order_text += f"⭐ *Points Earned:* {points}\n"
            order_text += f"🕐 *Time:* {order_data.get('timestamp', 'N/A')}\n\n"
            order_text += "✅ Order confirmed! Prepare for delivery."
            
            # Send notification to seller
            await context.bot.send_message(
                chat_id=SELLER_CHAT_ID,
                text=order_text,
                parse_mode="Markdown"
            )
            
            # Send confirmation back to customer (optional)
            await update.message.reply_text(
                f"✅ Thank you for your order! Total: ${total}\n"
                f"You earned {points} loyalty points! 🎉"
            )
            
            logging.info(f"Order processed for {customer_name}: ${total}")
            
        except Exception as e:
            logging.error(f"Error processing order: {e}")
            await update.message.reply_text("⚠️ There was an error processing your order.")
    else:
        # Regular text message handling (optional)
        await update.message.reply_text("Welcome! Use the menu button to place an order.")

def main():
    """Start the bot."""
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Handler for web_app_data (orders from Mini App)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_order))
    
    print("🤖 Bot is running... Waiting for orders...")
    app.run_polling(allowed_updates=["message"])

if __name__ == "__main__":
    main()