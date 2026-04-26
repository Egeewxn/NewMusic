from pyrogram import Client
from pytgcalls import GroupCallFactory
from config import API_ID, API_HASH, BOT_TOKEN, STRING_SESSION

# Ana Bot Kontrolü
app = Client("JazeBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Asistan (String Session)
asistan = Client("JazeAsistan", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)

# Ses Motoru
pytgcalls = GroupCallFactory(asistan).get_group_call()
