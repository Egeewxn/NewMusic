# GitHub'daki main.py dosyanın başı tam olarak böyle olmalı:
import sys
import os
import asyncio
from pyrogram import filters, idle
from pytgcalls import PyTgCalls
from pytgcalls import media  # types yerine media kullanıyoruz
from yt_dlp import YoutubeDL
# ... (kodun geri kalanı)

# Proje dosyaların
from config import *
from callsmusic.callsmusic import app, asistan

# --- VERİLER ---
queue = {}

call_py = PyTgCalls(app)

# --- YARDIMCI FONKSİYONLAR ---
def add_to_queue(chat_id, url, title):
    if chat_id not in queue:
        queue[chat_id] = []
    queue[chat_id].append({"url": url, "title": title})
    return len(queue[chat_id])

async def play_next(chat_id):
    if chat_id in queue and len(queue[chat_id]) > 0:
        next_track = queue[chat_id][0]
        await call_py.play(chat_id, media.AudioPiped(next_track["url"]))
    else:
        await call_py.leave_call(chat_id)

# --- YETKİ KOMUTLARI (SADECE OWNER) ---
@app.on_message(filters.command(["auth", "unauth", "authall"]) & filters.group)
async def auth_manager_h(_, m):
    if m.from_user.id != OWNER_ID:
        return await m.reply("❌ **Bu komutlar sadece sahibime özeldir.**")
    await m.reply("✅ **Yetki sistemi şu an devre dışı (Herkes kullanabilir).**")

# --- MÜZİK KOMUTLARI (HERKESE AÇIK) ---

@app.on_message(filters.command("oynat") & filters.group)
async def play_h(_, m):
    chat_id = m.chat.id
    query = " ".join(m.command[1:])
    if not query: return await m.reply("Şarkı adı yaz kanka!")
    
    proc = await m.reply("🔍 **Aranıyor...**")
    try:
        ydl_opts = {"format": "bestaudio", "quiet": True, "noplaylist": True}
        with YoutubeDL(ydl_opts) as ytdl:
            info = ytdl.extract_info(f"ytsearch:{query}", download=False)["entries"][0]
            url, title = info['url'], info['title']

        q_pos = add_to_queue(chat_id, url, title)
        if q_pos == 1:
            await call_py.play(chat_id, media.AudioPiped(url))
            await m.reply(f"▶ **Çalıyor:** {title}")
        else:
            await m.reply(f"✅ **Sıraya Eklendi:** {title}\n✨ **Sıra:** {q_pos-1}")
    except Exception as e:
        await m.reply(f"❌ **Hata:** {e}")
    await proc.delete()

@app.on_message(filters.command(["atla", "durdur", "devam", "son"]) & filters.group)
async def control_h(_, m):
    # Herhangi bir yetki kontrolü yok, gruptaki herkes kullanabilir.
    cmd = m.command[0]
    chat_id = m.chat.id
    try:
        if cmd == "atla":
            if chat_id in queue and len(queue[chat_id]) > 1:
                queue[chat_id].pop(0)
                await play_next(chat_id)
                await m.reply("⏭ **Sıradaki şarkıya geçildi.**")
            else:
                if chat_id in queue: queue[chat_id] = []
                await call_py.leave_call(chat_id)
                await m.reply("📡 **Akış bitti.**")
        elif cmd == "son":
            queue[chat_id] = []
            await call_py.leave_call(chat_id)
            await m.reply("⏹ **Tüm akış durduruldu.**")
        elif cmd == "durdur":
            await call_py.pause_stream(chat_id)
            await m.reply("⏸ **Duraklatıldı.**")
        elif cmd == "devam":
            await call_py.resume_stream(chat_id)
            await m.reply("▶ **Devam ettiriliyor.**")
    except Exception as e:
        await m.reply(f"❌ **Hata:** {e}")

# --- BAŞLATMA ---
async def start_jaze():
    print("⏳ Jaze Music Başlatılıyor...")
    await app.start()
    await asistan.start()
    await call_py.start()
    print("🚀 Jaze Music Online!")
    await idle()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(start_jaze())
    
