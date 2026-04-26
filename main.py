import asyncio
from pyrogram import filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from yt_dlp import YoutubeDL
from config import *
from callsmusic.callsmusic import app, asistan, pytgcalls

# --- YETKİ KONTROLÜ ---
async def can_manage_vc(chat_id, user_id):
    # Owner ve Sudo her zaman yetkili
    if user_id in SUDO_USERS: return True
    # Grupta auth almış mı?
    if user_id in AUTH_USERS.get(chat_id, []): return True
    # Grupta "Sesli Sohbeti Yönet" yetkisi var mı?
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
        await q.message.edit_caption("👑 **Kurucu Komutları:** /mban, /munban, /ekle\n\n*(Atla, Son, Durdur gibi komutlar VC yetkililerine özeldir)*", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Geri", callback_data="menu_ana")]]))
    elif q.data == "s_back":
        await q.message.edit_caption("▶ **Ben yararlı bir sesli sohbet botuyum.**", reply_markup=START_BTN)

# --- OWNER ÖZEL KOMUTLAR ---
@app.on_message(filters.command("mban") & filters.user(OWNER_ID))
async def ban_h(_, m):
    uid = int(m.command[1]); BANNED_USERS.append(uid)
    await m.reply(f"🚫 {uid} banlandı.")

@app.on_message(filters.command("munban") & filters.user(OWNER_ID))
async def unban_h(_, m):
    uid = int(m.command[1])
    if uid in BANNED_USERS: BANNED_USERS.remove(uid)
    await m.reply(f"✅ {uid} banı açıldı.")

@app.on_message(filters.command("ekle") & filters.user(OWNER_ID))
async def sudo_h(_, m):
    uid = int(m.command[1]); SUDO_USERS.append(uid)
    await m.reply(f"⭐ {uid} Sudo yapıldı.")

# --- OYNATMA (HERKES AÇABİLİR) ---
@app.on_message(filters.command(["oynat", "voynat"]) & filters.group)
async def play_h(_, m):
    if m.from_user.id in BANNED_USERS: return
    query = " ".join(m.command[1:])
    if not query: return await m.reply("İsim yaz kanka!")
    
    try: await asistan.get_chat_member(m.chat.id, "me")
    except: return await m.reply("⏳ **Asistan Hesabı Bekleniyor...**")

    proc = await m.reply("🔍 **YouTube'da Aranıyor...**")
    ydl_opts = {"format": "bestaudio" if m.command[0]=="oynat" else "best", "quiet": True, "outtmpl": "downloads/%(id)s.%(ext)s"}
    with YoutubeDL(ydl_opts) as ytdl:
        info = ytdl.extract_info(f"ytsearch:{query}", download=True)["entries"][0]
        file = ytdl.prepare_filename(info)

    if not pytgcalls.is_connected: await pytgcalls.join(m.chat.id)
    await pytgcalls.change_stream(file)
    await m.reply_photo(photo=THUMB_IMG, caption=f"✅ **Yayında:** {info['title']}\n👤 **İsteyen:** {m.from_user.mention}")
    await proc.delete()

# --- YETKİLİ KOMUTLARI (ATLA, SON, DURDUR, DEVAM) ---
@app.on_message(filters.command(["atla", "son", "durdur", "devam"]) & filters.group)
async def auth_cmds_h(_, m):
    if not await can_manage_vc(m.chat.id, m.from_user.id):
        return await m.reply("❌ Yetkin yok kanka. (VC yetkisi veya /auth lazım)")
    
    cmd = m.command[0]
    if cmd == "son":
        await pytgcalls.leave_current_group_call()
        await m.reply_photo(photo=THUMB_IMG, caption=f"📡 **Yayın Akışı Bitti Bot Sesten Ayrılıyor**\n👤 **Yapan:** {m.from_user.mention}")
    elif cmd == "atla": await m.reply("⏭ Atlandı.")
    elif cmd == "durdur": await pytgcalls.pause_stream(); await m.reply("⏸ Durduruldu.")
    elif cmd == "devam": await pytgcalls.resume_stream(); await m.reply("▶ Devam ediyor.")

# --- GRUP ÖZEL AUTH SİSTEMİ ---
@app.on_message(filters.command("auth") & filters.group)
async def auth_add_h(_, m):
    # Sadece grupta admin ekleme yetkisi olanlar auth verebilir
    check = await app.get_chat_member(m.chat.id, m.from_user.id)
    if not (check.privileges.can_promote_members or m.from_user.id in SUDO_USERS):
        return await m.reply("❌ Sadece admin ekleyebilenler /auth verebilir.")
    
    if m.reply_to_message: target = m.reply_to_message.from_user.id
    else: target = int(m.command[1])
    
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
    await app.start()
    await asistan.start()
    await pytgcalls.start() # Ses motorunu başlat
    print("🚀 Jaze Music v2 Online!")
    await idle()
    
