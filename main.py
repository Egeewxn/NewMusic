import sys
import os
import asyncio

# Kütüphane yollarını garantiye alalım
sys.path.append("/usr/local/lib/python3.8/dist-packages")
os.environ["PATH"] += os.pathsep + "/usr/bin"
os.environ["PATH"] += os.pathsep + "/usr/local/bin"

from pyrogram import filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# YENİ SÜRÜM (v3 dev) IMPORT YAPISI:
from pytgcalls import PyTgCalls
from pytgcalls import media  # AudioPiped ve VideoPiped artık buradan geliyor
from yt_dlp import YoutubeDL

# Config ve uygulama dosyalarından çekilenler
from config import *
from callsmusic.callsmusic import app, asistan

# pytgcalls nesnesini yeni sürüme göre tanımlayalım
call_py = PyTgCalls(app)

# --- START MENÜSÜ ---
START_BTN = InlineKeyboardMarkup([
    [InlineKeyboardButton("👤 Sahibim", url="https://t.me/yikmaz"),
     InlineKeyboardButton("🆘 Destek", url="https://t.me/l7xsohbet")],
    [InlineKeyboardButton("📚 Komutlar", callback_data="menu_ana")]
])

@app.on_message(filters.command("start") & filters.private)
async def start_h(_, m):
    await m.reply_photo(photo=THUMB_IMG, caption="▶ **Ben Jaze Music! Sesli sohbetlerde müzik çalabilirim.**", reply_markup=START_BTN)

@app.on_callback_query()
async def cb_h(_, q: CallbackQuery):
    if q.data == "menu_ana":
        btn = [[InlineKeyboardButton("🎵 Müzik Komutları", callback_data="u_cmds")],
               [InlineKeyboardButton("🔙 Geri", callback_data="s_back")]]
        await q.message.edit_caption("📚 **Komut Listesi**", reply_markup=InlineKeyboardMarkup(btn))
    elif q.data == "u_cmds":
        await q.message.edit_caption("🎵 **Komutlar:**\n\n/oynat - Şarkı\n/voynat - Video\n/atla - Kapatır\n/durdur - Durdurur\n/devam - Devam\n/son - Bitirir", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Geri", callback_data="menu_ana")]]))
    elif q.data == "s_back":
        await q.message.edit_caption("▶ **Ben Jaze Music! Sesli sohbetlerde müzik çalabilirim.**", reply_markup=START_BTN)

# --- OYNATMA SİSTEMİ ---
@app.on_message(filters.command(["oynat", "voynat"]) & filters.group)
async def play_h(_, m):
    if m.from_user.id in BANNED_USERS: return
    query = " ".join(m.command[1:])
    if not query: return await m.reply("İsim yaz kanka!")
    
    proc = await m.reply("🔍 **Akış aranıyor..**")
    
    ydl_opts = {"format": "bestaudio" if m.command[0]=="oynat" else "best", "quiet": True, "noplaylist": True}
    
    try:
        with YoutubeDL(ydl_opts) as ytdl:
            info = ytdl.extract_info(f"ytsearch:{query}", download=False)["entries"][0]
            url = info['url']

        # Yeni sürümde media.AudioPiped şeklinde kullanılır
        stream_type = media.AudioPiped(url) if m.command[0]=="oynat" else media.VideoPiped(url)
        
        await call_py.join_group_call(m.chat.id, stream_type)
        await m.reply_photo(photo=THUMB_IMG, caption=f"✅ **Yayında:** {info['title']}")
    except Exception as e:
        await m.reply(f"❌ **Hata:** {e}")
    
    await proc.delete()

# --- MÜZİK KONTROLLERİ ---
@app.on_message(filters.command(["atla", "son", "durdur", "devam"]) & filters.group)
async def music_logic_h(_, m):
    cmd = m.command[0]
    try:
        if cmd in ["son", "atla"]:
            await call_py.leave_group_call(m.chat.id)
            await m.reply("📡 **Yayın bitti.**")
        elif cmd == "durdur": 
            await call_py.pause_stream(m.chat.id)
            await m.reply("⏸ **Durduruldu.**")
        elif cmd == "devam": 
            await call_py.resume_stream(m.chat.id)
            await m.reply("▶ **Devam ediyor.**")
    except Exception as e:
        await m.reply(f"❌ **İşlem Hatası:** {e}")

# --- BAŞLATMA ---
async def start_jaze():
    print("⏳ Jaze Music Başlatılıyor (v3 dev)...")
    await app.start()
    await asistan.start()
    await call_py.start()
    print("🚀 Jaze Music v2 Online!")
    await idle()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(start_jaze())
    
