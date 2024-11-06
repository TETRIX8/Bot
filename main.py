import os 
import hmac 
import hashlib 
import requests 
import time 
from aiogram import Bot, Dispatcher, types 
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup 
from aiogram.utils import executor 
from aiogram.dispatcher.filters import CommandStart 
from dotenv import load_dotenv 
 
load_dotenv() 
 
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") 
MEXC_ACCESS_KEY = os.getenv("MEXC_ACCESS_KEY") 
MEXC_SECRET_KEY = os.getenv("MEXC_SECRET_KEY") 
 
# Default parameters 
DEFAULT_BUY_AMOUNT = 1 
DEFAULT_PROFIT_PERCENT = 0.03 
DEFAULT_DROP_PERCENT = 0.01 
 
# Global variables 
buy_amount = DEFAULT_BUY_AMOUNT 
profit_percent = DEFAULT_PROFIT_PERCENT 
drop_percent = DEFAULT_DROP_PERCENT 
auto_buy_active = False 
 
# Bot and dispatcher initialization 
bot = Bot(token=TELEGRAM_BOT_TOKEN) 
dp = Dispatcher(bot) 
 
def sign(query_string: str) -> str: 
    '''Generate signature for MEXC API request''' 
    return hmac.new(MEXC_SECRET_KEY.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest() 
 
async def new_order(symbol: str, side: str, order_type: str, quantity: int = None): 
    '''Send a new order to the MEXC API''' 
    timestamp = int(time.time() * 1000) 
    query_string = f"symbol={symbol}&side={side}&type={order_type}&timestamp={timestamp}" 
    if quantity: 
        query_string += f"&quantity={quantity}" 
    signature = sign(query_string) 
    url = f"https://api.mexc.com/api/v3/order?{query_string}&signature={signature}" 
    headers = { 
        "X-MEXC-APIKEY": MEXC_ACCESS_KEY 
    } 
    response = requests.post(url, headers=headers) 
    return response.json() 
 
@dp.message_handler(commands=['start']) 
async def start(message: types.Message): 
    '''Start command handler''' 
    keyboard = InlineKeyboardMarkup() 
    keyboard.add(InlineKeyboardButton("Start Auto-Buy", callback_data="start_auto_buy")) 
    await message.answer("Welcome! Use the buttons below to control the bot.", reply_markup=keyboard) 
 
@dp.callback_query_handler(lambda c: c.data == 'start_auto_buy') 
async def process_callback_start_auto_buy(callback_query: types.CallbackQuery): 
    '''Callback handler for starting auto-buy''' 
    global auto_buy_active 
    auto_buy_active = True 
    await bot.answer_callback_query(callback_query.id) 
    await bot.send_message(callback_query.from_user.id, "Auto-buy has been activated!") 
 
@dp.message_handler(commands=['set_buy_amount']) 
async def set_buy_amount(message: types.Message): 
    '''Command handler for setting buy amount''' 
    global buy_amount 
    try: 
        buy_amount = float(message.text.split()[1]) 
        await message.reply(f"Buy amount set to {buy_amount}") 
    except (IndexError, ValueError): 
        await message.reply("Please provide a valid amount. Usage: /set_buy_amount <amount>") 
 
# Other handlers here... 
 
if __name__ == '__main__': 
    executor.start_polling(dp, skip_updates=True) 
    print("Bot token:", TELEGRAM_BOT_TOKEN)  # Убедитесь, что токен корректен и не
