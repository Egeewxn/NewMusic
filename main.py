import sys
import os
import asyncio

# --- SİSTEM YOLLARINI ZORLA TANIMLAMA ---
sys.path.append("/usr/local/lib/python3.8/dist-packages")
os.environ["PATH"] += os.pathsep + "/usr/bin"
os.environ["PATH"] += os.pathsep + "/usr/local/bin"

from pyrogram import filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped, VideoPiped
from yt_dlp import YoutubeDL
from config import *
from callsmusic.callsmusic import app, asistan, pytgcalls

# --- MENÜLER ---
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
        await q.message.edit_caption("🎵 **Komutlar:**\n\n/oynat - Şarkı çalar\n/voynat - Video çalar\n/atla - Sıradakine geçer\n/durdur - Müziği durdurur\n/devam - Müziği devam ettirir\n/son - Yayını bitirir", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Geri", callback_data="menu_ana")]]))
    elif q.data == "s_back":
        await q.message.edit_caption("▶ **Ben Jaze Music! Sesli sohbetlerde müzik çalabilirim.**", reply_markup=START_BTN)

# --- OYNATMA SİSTEMİ ---
@app.on_message(filters.command(["oynat", "voynat"]) & filters.group)
async def play_h(_, m):
    if m.from_user.id in BANNED_USERS: return
    query = " ".join(m.command[1:])
    if not query: return await m.reply("İsim yaz kanka!")
    
    proc = await m.reply("🔍 **Akış aranıyor..**")
    
    ydl_opts = {
        "format": "bestaudio" if m.command[0]=="oynat" else "best",
        "quiet": True, 
        "outtmpl": "downloads/%(id)s.%(ext)s",
        "noplaylist": True
    }
    
    try:
        with YoutubeDL(ydl_opts) as ytdl:
            info = ytdl.extract_info(f"ytsearch:{query}", download=True)["entries"][0]
            file = ytdl.prepare_filename(info)

        stream_type = AudioPiped(file) if m.command[0]=="oynat" else VideoPiped(file)
        
        await pytgcalls.join_group_call(m.chat.id, stream_type)
        await m.reply_photo(photo=THUMB_IMG, caption=f"✅ **Yayında:** {info['title']}\n👤 **İsteyen:** {m.from_user.mention}")
    except Exception as e:
        await m.reply(f"❌ **Hata:** {e}")
    
    await proc.delete()

# --- TEMEL MÜZİK KONTROL KOMUTLARI ---
@app.on_message(filters.command(["atla", "son", "durdur", "devam"]) & filters.group)
async def music_logic_h(_, m):
    # Banlı değilse herkes kullanabilir (veya istersen SUDO_USERS kontrolü ekleyebilirsin)
    if m.from_user.id in BANNED_USERS: return
    
    cmd = m.command[0]
    try:
        if cmd == "son":
            await pytgcalls.leave_group_call(m.chat.id)
            await m.reply("📡 **Yayın sonlandırıldı.**")
        elif cmd == "durdur": 
            await pytgcalls.pause_stream(m.chat.id)
            await m.reply("⏸ **Yayın duraklatıldı.**")
        elif cmd == "devam": 
            await pytgcalls.resume_stream(m.chat.id)
            await m.reply("▶ **Yayın devam ediyor.**")
        elif cmd == "atla":
            # Şimdilik yayını sonlandırıp mesaj atar, sıra sistemi kurulduğunda otomatik geçer.
            await pytgcalls.leave_group_call(m.chat.id)
            await m.reply("⏭ **Şarkı atlandı.**")
    except Exception as e:
        await m.reply(f"❌ **İşlem yapılamadı:** {e}")

# --- BAŞLATMA ---
async def start_jaze():
    print("⏳ Jaze Music Başlatılıyor (Auth Sistemi Kaldırıldı)...")
    await app.start()
    await asistan.start()
    await pytgcalls.start()
    print("🚀 Jaze Music v2 Online! (Sadece Müzik)")
    await idle()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(start_jaze())
    
