from pyrogram import Client
from pytgcalls import PyTgCalls
from config import API_ID, API_HASH, BOT_TOKEN, STRING_SESSION

# Ana Bot
app = Client("JazeBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Asistan (String Session)
asistan = Client("JazeAsistan", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)

# Yeni Nesil Ses Motoru
pytgcalls = PyTgCalls(asistan)
