import logging
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TOKEN = "8452975233:AAG-JdJ_0XBspAVj7xKRzbTSdtT0sWz4B-k"
WEB_APP_URL = "https://phearun-ean.github.io/tgminiapp/"  # Your hosted mini app URL

# Database simulation (use real database in production)
orders_db = {}
users_db = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message with mini app button."""
    user = update.effective_user
    
    # Store user info
    users_db[user.id] = {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'username': user.username,
        'joined_date': datetime.now().isoformat(),
        'orders': [],
        'points': 0
    }
    
    welcome_message = (
        f"🍔 *Welcome to Durger King, {user.first_name}!*\n\n"
        "Order delicious burgers right from Telegram!\n"
        "✓ Real-time order tracking\n"
        "✓ Loyalty points system\n"
        "✓ Special deals for members\n"
        "✓ Fast delivery"
    )
    
    keyboard = [[
        InlineKeyboardButton(
            text="🍔 Open Durger King",
            web_app=WebAppInfo(url=WEB_APP_URL)
        )
    ]]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle data received from the mini app."""
    try:
        data = json.loads(update.effective_message.web_app_data.data)
        user = update.effective_user
        
        logger.info(f"Received order from user {user.id}: {data}")
        
        # Store order in database
        order_id = f"ORD{len(orders_db) + 1:04d}"
        orders_db[order_id] = {
            'user_id': user.id,
            'user_name': f"{user.first_name} {user.last_name or ''}",
            'items': data.get('items', []),
            'total': data.get('total'),
            'points_earned': data.get('points', 0),
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'status': 'confirmed'
        }
        
        # Update user points
        if user.id not in users_db:
            users_db[user.id] = {'points': 0, 'orders': []}
        
        users_db[user.id]['points'] = users_db[user.id].get('points', 0) + data.get('points', 0)
        users_db[user.id]['orders'].append(order_id)
        
        # Create order summary
        items_list = "\n".join([f"• {item['name']} - ${item['price']:.2f}" for item in data.get('items', [])])
        
        order_summary = (
            f"✅ *Order Confirmed!*\n\n"
            f"*Order ID:* `{order_id}`\n"
            f"*Items:*\n{items_list}\n"
            f"*Total:* ${data.get('total', '0.00')}\n"
            f"*Points Earned:* {data.get('points', 0)} 🌟\n"
            f"*Total Points:* {users_db[user.id]['points']} 🌟\n\n"
            f"Your order is being prepared! We'll notify you when it's ready."
        )
        
        await update.message.reply_text(
            order_summary,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Send admin notification (optional)
        await notify_admin(context, order_id, data)
        
    except Exception as e:
        logger.error(f"Error processing web app data: {e}")
        await update.message.reply_text(
            "Sorry, there was an error processing your order. Please try again."
        )

async def notify_admin(context: ContextTypes.DEFAULT_TYPE, order_id: str, order_data: dict):
    """Send notification to admin channel."""
    admin_chat_id = "455774531"  # Set your admin chat ID
    
    admin_message = (
        f"🆕 *New Order!*\n\n"
        f"*Order ID:* {order_id}\n"
        f"*User:* {order_data.get('userName', 'Unknown')}\n"
        f"*Items:* {len(order_data.get('items', []))}\n"
        f"*Total:* ${order_data.get('total', '0.00')}\n"
        f"*Time:* {datetime.now().strftime('%H:%M:%S')}"
    )
    
    try:
        await context.bot.send_message(
            chat_id=admin_chat_id,
            text=admin_message,
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")

async def order_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check order status."""
    if not context.args:
        await update.message.reply_text(
            "Please provide an order ID. Example: /status ORD001"
        )
        return
    
    order_id = context.args[0].upper()
    
    if order_id in orders_db:
        order = orders_db[order_id]
        status_message = (
            f"📦 *Order Status*\n\n"
            f"*Order ID:* `{order_id}`\n"
            f"*Status:* {order['status']}\n"
            f"*Items:* {len(order['items'])} items\n"
            f"*Total:* ${order['total']}\n"
            f"*Placed:* {order['timestamp']}"
        )
    else:
        status_message = f"❌ Order {order_id} not found."
    
    await update.message.reply_text(status_message, parse_mode=ParseMode.MARKDOWN)

async def my_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check loyalty points."""
    user = update.effective_user
    points = users_db.get(user.id, {}).get('points', 0)
    
    points_message = (
        f"🌟 *Your Loyalty Points*\n\n"
        f"*Current Balance:* {points} points\n\n"
        f"*Redeem your points for:*\n"
        f"• 100 points → Free Fries 🍟\n"
        f"• 200 points → Free Durger 🍔\n"
        f"• 500 points → Free Meal Deal 🍱"
    )
    
    # Add redeem button
    keyboard = [[
        InlineKeyboardButton("🎁 Redeem Points", callback_data="redeem_points")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        points_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    "Open menu"
