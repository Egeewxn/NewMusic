import os
import sys
import asyncio

# --- FFMPEG YOLU TANIMLAMA (Hata Almamak İçin) ---
os.environ["PATH"] += os.pathsep + "/usr/bin"
os.environ["PATH"] += os.pathsep + "/usr/local/bin"

from pyrogram import filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pytgcalls.types import AudioPiped, VideoPiped
from yt_dlp import YoutubeDL
from config import *
from callsmusic.callsmusic import app, asistan, pytgcalls

# --- YETKİ KONTROLÜ ---
async def can_manage_vc(chat_id, user_id):
    if user_id in SUDO_USERS: return True
    if user_id in AUTH_USERS.get(chat_id, []): return True
    try:
        m = await app.get_chat_member(chat_id, user_id)
        return m.privileges.can_manage_video_chats if m.privileges else False
    except: return False

# --- MENÜLER ---
START_BTN = InlineKeyboardMarkup([
    [InlineKeyboardButton("👤 Sahibim", url="https://t.me/yikmaz"),
     InlineKeyboardButton("🆘 Destek", url="https://t.me/l7xsohbet")],
    [InlineKeyboardButton("📚 Komutlar", callback_data="menu_ana")]
])

@app.on_message(filters.command("start") & filters.private)
async def start_h(_, m):
    await m.reply_photo(photo=THUMB_IMG, caption="▶ **Ben yararlı bir sesli sohbet botuyum.**", reply_markup=START_BTN)

@app.on_callback_query()
async def cb_h(_, q: CallbackQuery):
    if q.data == "menu_ana":
        btn = [[InlineKeyboardButton("🎵 Komutlar", callback_data="u_cmds"), InlineKeyboardButton("👑 Admin", callback_data="a_cmds")],
               [InlineKeyboardButton("🔙 Geri", callback_data="s_back")]]
        await q.message.edit_caption("📚 **Jaze Music Menü**", reply_markup=InlineKeyboardMarkup(btn))
    elif q.data == "u_cmds":
        await q.message.edit_caption("🎵 **Komutlar:** /oynat, /voynat, /authall", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Geri", callback_data="menu_ana")]]))
    elif q.data == "a_cmds":
        await q.message.edit_caption("👑 **Kurucu Komutları:** /mban, /munban, /ekle", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Geri", callback_data="menu_ana")]]))
    elif q.data == "s_back":
        await q.message.edit_caption("▶ **Ben yararlı bir sesli sohbet botuyum.**", reply_markup=START_BTN)

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

# --- YETKİLİ KOMUTLARI ---
@app.on_message(filters.command(["atla", "son", "durdur", "devam"]) & filters.group)
async def auth_cmds_h(_, m):
    if not await can_manage_vc(m.chat.id, m.from_user.id):
        return await m.reply("❌ Yetkin yok kanka.")
    
    cmd = m.command[0]
    try:
        if cmd == "son":
            await pytgcalls.leave_group_call(m.chat.id)
            await m.reply_photo(photo=THUMB_IMG, caption=f"📡 **Yayın Bitti**\n👤 **Yapan:** {m.from_user.mention}")
        elif cmd == "durdur": 
            await pytgcalls.pause_stream(m.chat.id)
            await m.reply("⏸ Durduruldu.")
        elif cmd == "devam": 
            await pytgcalls.resume_stream(m.chat.id)
            await m.reply("▶ Devam ediyor.")
        elif cmd == "atla":
            await m.reply("⏭ Şarkı atlandı (Sıradaki sisteme eklendiğinde aktif olacak).")
    except Exception as e:
        await m.reply(f"❌ **İşlem Hatası:** {e}")

# --- OWNER VE AUTH KOMUTLARI ---
@app.on_message(filters.command("mban") & filters.user(OWNER_ID))
async def ban_h(_, m):
    try:
        uid = int(m.command[1])
        BANNED_USERS.append(uid)
        await m.reply(f"🚫 {uid} bot kullanımından banlandı.")
    except: await m.reply("ID yaz kanka.")

@app.on_message(filters.command("munban") & filters.user(OWNER_ID))
async def unban_h(_, m):
    try:
        uid = int(m.command[1])
        if uid in BANNED_USERS: BANNED_USERS.remove(uid)
        await m.reply(f"✅ {uid} banı kaldırıldı.")
    except: await m.reply("ID yaz kanka.")

@app.on_message(filters.command("auth") & filters.group)
async def auth_add_h(_, m):
    check = await app.get_chat_member(m.chat.id, m.from_user.id)
    if not (check.privileges.can_promote_members or m.from_user.id in SUDO_USERS):
        return await m.reply("❌ Sadece admin ekleyebilenler /auth verebilir.")
    
    target = m.reply_to_message.from_user.id if m.reply_to_message else int(m.command[1])
    if m.chat.id not in AUTH_USERS: AUTH_USERS[m.chat.id] = []
    AUTH_USERS[m.chat.id].append(target)
    await m.reply(f"✅ ID: {target} bu grup için yetkilendirildi.")

@app.on_message(filters.command("authall") & filters.group)
async def auth_list_h(_, m):
    text = f"📋 **{m.chat.title} Yetkilileri:**\n"
    users = AUTH_USERS.get(m.chat.id, [])
    if not users: text += "Henüz yetkili yok."
    for i, u in enumerate(users, 1): text += f"{i}. `{u}`\n"
    await m.reply(text)

# --- BAŞLATMA ---
async def start_jaze():
    print("⏳ Jaze Music Başlatılıyor...")
    await app.start()
    await asistan.start()
    await pytgcalls.start()
    print("🚀 Jaze Music v2 Online!")
    await idle()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_jaze())
