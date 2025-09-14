# bot.py - Telegram BIN Bot (pyTelegramBotAPI version)
# Usage: set TELEGRAM_BOT_TOKEN environment variable (Railway variables)
import os
import requests
import html
import logging
from urllib.parse import quote_plus, unquote_plus
import telebot
from telebot import types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") '7960622720:AAGqk5nBVrA0SoOgb4MOLDy-BemB3NNBeQc'
if not BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not set in environment. Exiting.")
    raise SystemExit("TELEGRAM_BOT_TOKEN not provided. Set env var in Railway or local env.")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

BASE = "https://smartxen.vercel.app/gen?bin={bin_value}"
TIMEOUT = 10
MAX_CARDS_SHOW = 20
MAX_CALLBACK_LEN = 60

def call_bin(api_bin: str):
    url = BASE.format(bin_value=quote_plus(api_bin))
    try:
        resp = requests.get(url, timeout=TIMEOUT)
    except requests.RequestException as e:
        logger.exception("HTTP request failed for %s", url)
        raise
    if resp.status_code != 200:
        raise RuntimeError(f"API returned status {resp.status_code}")
    try:
        return resp.json()
    except ValueError:
        return {"text": resp.text}

def normalize_field(field: str):
    return "".join((c if c.isdigit() or c.lower() == "x" else "x") for c in field)

def build_output_from_json(json_data: dict, clean_bin: str):
    bin_info = html.escape(str(json_data.get("BIN Info", "Unknown")))
    bank = html.escape(str(json_data.get("Bank", "Unknown")))
    country = html.escape(str(json_data.get("Country", "Unknown")))
    amount = html.escape(str(json_data.get("amount", 0)))
    cards = json_data.get("cards", []) or []
    shown_cards = cards[:MAX_CARDS_SHOW]
    formatted_cards = "\\n".join(f"<code>{html.escape(str(c))}</code>" for c in shown_cards)
    if len(cards) > MAX_CARDS_SHOW:
        formatted_cards += "\\n\\n<em>...and more</em>"

    bin_display = html.escape(clean_bin[:6])
    output = (
        f"𝗕𝗜𝗡 ⇾ <code>{bin_display}</code>\\n"
        f"𝗔𝗺𝗼𝘂𝗻𝘁 ⇾ <code>{amount}</code>\\n\\n"
        f"{formatted_cards}\\n\\n"
        f"𝗜𝗻𝗳𝗼: {bin_info}\\n"
        f"𝗕𝗮𝗻𝗸: {bank}\\n"
        f"𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {country}\\n"
    )
    return output

def parse_input(msg_text: str):
    # Remove command prefix
    userid_raw = msg_text.replace("/gen", "").replace(".gen", "").strip()
    for ch in ["/", ".", ",", "(", ")", " "]:
        userid_raw = userid_raw.replace(ch, "|")
    parts = [p.strip() for p in userid_raw.split("|") if p.strip()]
    clean_bin = "".join(ch for ch in (parts[0] if parts else "") if ch.isdigit())
    exp_month = normalize_field(parts[1]) if len(parts) >= 2 else ""
    exp_year  = normalize_field(parts[2]) if len(parts) >= 3 else ""
    cvc       = normalize_field(parts[3]) if len(parts) >= 4 else ""
    api_bin = clean_bin
    if exp_month and exp_year and cvc:
        api_bin = f"{clean_bin}|{exp_month}|{exp_year}|{cvc}"
    elif exp_month and exp_year:
        api_bin = f"{clean_bin}|{exp_month}|{exp_year}"
    return clean_bin, api_bin

@bot.message_handler(commands=['gen'])
def gen_command_handler(message):
    try:
        msg_text = message.text or ""
        # allow both "/gen" and ".gen" in message text
        if not (msg_text.startswith("/gen") or msg_text.startswith(".gen")):
            return
        clean_bin, api_bin = parse_input(msg_text)
        if not clean_bin:
            bot.send_message(chat_id=message.chat.id,
                             text="❌ <b>Please Send A Valid Bin</b>",
                             reply_to_message_id=message.message_id)
            return
        if len(clean_bin) < 6 or clean_bin[0] not in ('5', '4', '3', '6'):
            bot.send_message(chat_id=message.chat.id,
                             text="❌ <b>Please Sir Send A Valid Bin</b>",
                             reply_to_message_id=message.message_id)
            return
        try:
            json_data = call_bin(api_bin)
        except Exception as e:
            logger.exception("call_bin failed")
            bot.send_message(chat_id=message.chat.id,
                             text="⚠️ <b>API request failed. Try again later.</b>",
                             reply_to_message_id=message.message_id)
            return
        if isinstance(json_data, dict) and json_data.get("text") and not json_data.get("status"):
            txt = str(json_data.get("text"))[:4000]
            bot.send_message(chat_id=message.chat.id, text=html.escape(txt), reply_to_message_id=message.message_id)
            return
        if isinstance(json_data, dict) and json_data.get("status") == "success":
            output = build_output_from_json(json_data, clean_bin)
            safe_callback = quote_plus(api_bin)[:MAX_CALLBACK_LEN]
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text="Regenerate", callback_data=f"regen|{safe_callback}"))
            sent = bot.send_message(chat_id=message.chat.id, text=output, reply_markup=keyboard, reply_to_message_id=message.message_id)
            return
        else:
            bot.send_message(chat_id=message.chat.id,
                             text="⚠️ <b>API did not return success or returned unexpected data.</b>",
                             reply_to_message_id=message.message_id)
            return
    except Exception:
        logger.exception("Error in gen_command_handler")
        try:
            bot.send_message(chat_id=message.chat.id,
                             text="❌ <b>There was an internal error processing your request.</b>",
                             reply_to_message_id=message.message_id)
        except Exception:
            pass

@bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("regen|"))
def regen_callback(call):
    try:
        raw = call.data.split("|", 1)[1]
        api_bin = unquote_plus(raw)
        # call API again and edit message
        try:
            json_data = call_bin(api_bin)
        except Exception:
            bot.answer_callback_query(callback_query_id=call.id, text="API request failed.", show_alert=False)
            return
        # if success, build output and edit
        # get clean_bin for display
        clean_bin = api_bin.split("|", 1)[0] if api_bin else ""
        if isinstance(json_data, dict) and json_data.get("status") == "success":
            output = build_output_from_json(json_data, clean_bin)
            try:
                bot.edit_message_text(chat_id=call.message.chat.id,
                                      message_id=call.message.message_id,
                                      text=output)
                bot.answer_callback_query(callback_query_id=call.id, text="Regenerated.", show_alert=False)
            except Exception:
                # editing might fail if content unchanged or too long; just answer callback
                bot.answer_callback_query(callback_query_id=call.id, text="Updated (couldn't edit message).", show_alert=False)
        else:
            bot.answer_callback_query(callback_query_id=call.id, text="API returned unexpected data.", show_alert=False)
    except Exception:
        logger.exception("Error in regen_callback")
        try:
            bot.answer_callback_query(callback_query_id=call.id, text="Internal error.", show_alert=False)
        except Exception:
            pass

if __name__ == '__main__':
    logger.info("Bot started...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)