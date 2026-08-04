# -*- coding: utf-8 -*-
"""
بوتی زیرەک - Telegram Group Voice Chat Call Music & Groq AI Bot in Python
"""

import os
import sys
import re
import json
import random
import asyncio
import requests
from pathlib import Path

from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
from pytgcalls import GroupCallFactory
import yt_dlp
import groq

# Credentials
API_ID = 33605478
API_HASH = "0026515a5d113337a0878ed2e6b1be10"
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

app = Client(
    "zirak_bot_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Monkeypatch Pyrogram v2 client.send for PyTgCalls compatibility
app.send = app.invoke

group_call_factory = GroupCallFactory(app)
group_call = group_call_factory.get_file_group_call()

groq_client = groq.Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

STATE_FILE = Path("data/state.json")
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

if STATE_FILE.exists():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state_data = json.load(f)
    except Exception:
        state_data = {"warnings": {}, "ai_history": {}}
else:
    state_data = {"warnings": {}, "ai_history": {}}

def save_state():
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state_data, f, ensure_ascii=False, indent=2)

AI_SYSTEM_PROMPT = """
You are Zirak (زیرەک), a friendly, intelligent young Kurdish guy in a Telegram group chat.
You speak only in short, natural, human Sorani Kurdish (کوردیی سۆرانی ئاسایی چات).

Strict Rules:
1. NEVER translate machine English into Kurdish. Never use broken literal dictionary words.
2. Respond in 1 short, natural sentence as a real Kurdish friend in chat.
3. Use everyday Kurdish chat phrases (وەڵا, گیان, کاکە, ئاساییە, عافیەت بێت, هههه).
4. Be witty, friendly, and respectful.

Examples:
User: سڵاو چۆنیت؟
Zirak: سڵاو لە تۆش گیان! من زۆر باشم، تۆ چۆنیت؟

User: ئەمە چییە؟
Zirak: ئەمە چاتی گروپەکەمانە گیان، چی پرسیارێکت هەیە فەرموو!

User: بۆ وا قسە ئەکەی؟
Zirak: هههه بەخوا من ئاسایی قسە ئەکەم، وەک هاوڕێیەکی نزیک چات ئەکەم لەگەڵت!

User: حەسەن زیرەک چی بوو؟
Zirak: حەسەن زیرەک گەورەترین و بەناوبانگترین گۆرانیبێژی ڕەسەنی کوردی بوو!
"""

SMART_REPLIES = [
    {
        "patterns": ["سڵاو", "سلاو", "سلام", "هەڵۆ", "hello", "hi"],
        "replies": ["سڵاو لە تۆش گیان! ❤️", "سڵاو بەخێر بێیت! 🌸", "سڵاو چۆنیت؟ 😊", "سڵاو و ڕێز بۆ تۆی بەڕێز 💖"]
    },
    {
        "patterns": ["چۆنیت", "چونیت", "چۆنی", "چاکیت", "باشیت", "چ هەواڵ"],
        "replies": ["سوپاس بۆ خوا من زۆر باشم، تۆ چۆنیت گیان؟ ✨", "زۆر باشم سوپاس! تۆ بڵێ چی هەیە؟ 😊", "سوپاس گەورەم، من باشم تۆ چۆنیت؟ ❤️"]
    },
    {
        "patterns": ["دەستت خۆش", "دەست خۆش", "دەستت کەڵەک پێ بێت", "دەستت ڕەنگین"],
        "replies": ["عافیەتت بێت گیانەکەم! ❤️", "سەرکەوتوو بیت، شایەنی نییە 🌸", "دەستی تۆش خۆش بێت براکەم ✨"]
    },
    {
        "patterns": ["سوپاس", "سوپاست دەکەم", "دەستت خۆش بیت"],
        "replies": ["شایەنی نییە گیانەکەم! ❤️", "بەردەوام لە خزمەتین! 🌸", "سەرچاوم! ✨"]
    },
    {
        "patterns": ["ناوی تۆ چییە", "ناوت چییە", "تۆ کێیت", "کێیت"],
        "replies": ["من ناوم زیرەکە! هاوڕێیەکی دڵسۆزی کوردم لەم گروپەدا 🤖❤️", "من زیرەکم! خزمەتکاری ئێوەی ئازیز 🌸"]
    }
]

WELCOME_MESSAGES = [
    "🌸 سڵاو {name} گیان! زۆر بەخێر هاتیت بۆ گروپەکەمان 🎉\n\nگەرمترین بەخێرهاتنت لێ دەکەین، هیواین کاتێکی زۆر خۆش لەگەڵمان بەسەر بپەڕێنیت! ✨❤️",
    "👑 سڵاو لە {name} خۆشەویست! زۆر بەخێربێیت بۆ نێو خێزانەکەمان 🌟\n\nخۆشحالین بە هاتنت! 🌺",
    "✨ سڵاو و دەرەکەت خۆش {name} گیان! بەخێربێیت بەسەر چاوانمان 💐\n\nگروپ بە هاتنی تۆ ڕووناک بووەوە! 🎉"
]

BAD_WORDS = [
    r'fuck', r'f\s*u\s*c\s*k', r'shit', r'bitch', r'asshole', r'dick', r'pussy',
    r'bastard', r'whore', r'slut', r'nigger', r'faggot', r'cock', r'cunt',
    r'motherf', r'stfu', r'porn', r'xxx', r'nude', r'naked'
]

NSFW_DOMAINS = [
    r'pornhub\.com', r'xvideos\.com', r'xnxx\.com', r'xhamster\.com',
    r'redtube\.com', r'youporn\.com', r'brazzers\.com', r'onlyfans\.com'
]

def get_smart_reply(text: str):
    lower = text.strip().lower()
    for entry in SMART_REPLIES:
        for p in entry["patterns"]:
            if p in lower:
                return random.choice(entry["replies"])
    return None

def clean_ai_text(text: str) -> str:
    if not text:
        return ""
    clean = re.sub(r'(?im)^\s*@?[a-zA-Z0-9_]+:\s*', '', text)
    clean = re.sub(r'\([^()\r\n]*\)', '', clean)
    if re.search(r'[\u0900-\u097F]', clean):
        return ""
    return clean.strip()

def get_ai_reply(chat_id: int, user_id: int, question: str) -> str:
    smart = get_smart_reply(question)
    if smart:
        return smart

    if not groq_client:
        return "گیان دووبارە ڕوونی بکەرەوە 😅"

    try:
        res = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": AI_SYSTEM_PROMPT},
                {"role": "user", "content": question}
            ],
            max_tokens=120,
            temperature=0.5
        )
        answer = res.choices[0].message.content
        answer = clean_ai_text(answer)
        if answer:
            return answer
    except Exception as e:
        print("Groq Error:", e)

    return "گیان دەتوانیت دووبارە ڕوونی بکەیتەوە؟ 😅"

DOWNLOADS_DIR = Path("downloads")
DOWNLOADS_DIR.mkdir(exist_ok=True)

def download_youtube_audio(query_or_url: str):
    search_target = query_or_url if query_or_url.startswith("http") else f"ytsearch1:{query_or_url}"
    file_id = os.urandom(8).hex()
    out_template = str(DOWNLOADS_DIR / f"{file_id}.%(ext)s")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': out_template,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'max_filesize': 25000000
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_target, download=True)
        if 'entries' in info and len(info['entries']) > 0:
            info = info['entries'][0]
        
        file_path = ydl.prepare_filename(info)
        title = info.get('title', 'گۆرانیی داواکراو')
        return file_path, title

@app.on_message(filters.command(["start", "help"]))
async def start_cmd(client: Client, message: Message):
    text = (
        f"سڵاو {message.from_user.first_name} گیان! من زیرەکم 🤖\n\n"
        "🎵 **فرمانەکانی گۆرانی لە ناو کاڵ (Group Voice Chat Call):**\n"
        "• `/play ناوی گۆرانی یان لینک` - جۆین بوونی کاڵ و پەخشکردنی گۆرانی\n"
        "• `/pause` - ڕاگرتنی کاتیی گۆرانی لە کاڵ\n"
        "• `/resume` - بەردەوامبوونی گۆرانی لە کاڵ\n"
        "• `/stop` یان `/leave` - ڕاگرتن و دەرچوون لە کاڵ\n\n"
        "💬 ئەوانەی تر تەنها قسەم لەگەڵ بکە و من بە کوردیی زۆر باڵا جوابت دەدەمەوە!"
    )
    await message.reply_text(text)

@app.on_message(filters.command(["play", "gorani", "music"]))
async def play_music_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    query = message.text.split(maxsplit=1)
    
    if len(query) < 2:
        await message.reply_text("تکایە لینکی یوتوب یان ناوی گۆرانییەک بنووسە!\n\nنمونە:\n`/play https://www.youtube.com/watch?v=...`\n`/play شێروان عەبدوڵا`")
        return

    query_str = query[1]
    msg = await message.reply_text("⏳ لەسەر داوای تۆ جۆینی کاڵەکە دەبم و گۆرانییەکە دەهێنم... 🎵")

    try:
        file_path, title = await asyncio.to_thread(download_youtube_audio, query_str)
        
        group_call.input_filename = file_path
        if not group_call.is_connected:
            await group_call.start(chat_id)
        
        await msg.edit_text(f"🎵 **ئێستا لە ناو کاڵەکەدا (Group Voice Call) پەخش دەبێت:**\n**{title}**\n\nبۆ ڕاگرتن: `/pause` | بۆ دەستپێکردنەوە: `/resume` | بۆ دەرچوون: `/stop`")
    except Exception as e:
        print("Play Error:", e)
        await msg.edit_text(f"ببوورە گیان! کێشەیەک ڕوویدا لە جۆین بوونی کاڵەکە یان داگرتنی گۆرانی: {e}\n\nدڵنیا ببەوە کە کاڵ (Group Voice Call) کراوەتەوە لە گروپەکەدا و بوتەکە ئەدمینە!")

@app.on_message(filters.command(["pause"]))
async def pause_cmd(client: Client, message: Message):
    try:
        group_call.pause_playout()
        await message.reply_text("⏸️ گۆرانییەکە لە کاڵەکەدا ڕاوەستا.")
    except Exception as e:
        await message.reply_text(f"کێشەیەک هەیە: {e}")

@app.on_message(filters.command(["resume"]))
async def resume_cmd(client: Client, message: Message):
    try:
        group_call.resume_playout()
        await message.reply_text("▶️ گۆرانییەکە دەستی پێ کردەوە.")
    except Exception as e:
        await message.reply_text(f"کێشەیەک هەیە: {e}")

@app.on_message(filters.command(["stop", "leave"]))
async def stop_cmd(client: Client, message: Message):
    try:
        group_call.stop()
        await message.reply_text("⏹️ لە کاڵەکە دەرباز بووم و گۆرانییەکە ڕاوەستا.")
    except Exception as e:
        await message.reply_text(f"کێشەیەک هەیە: {e}")

@app.on_message(filters.new_chat_members)
async def welcome_member(client: Client, message: Message):
    for member in message.new_chat_members:
        if member.is_bot:
            continue
        w = random.choice(WELCOME_MESSAGES).format(name=member.first_name)
        await message.reply_text(w)

@app.on_message(filters.text & ~filters.bot)
async def chat_handler(client: Client, message: Message):
    text = message.text
    if text.startswith("/"):
        return

    # Bad words & NSFW filter
    for pattern in BAD_WORDS:
        if re.search(pattern, text, re.IGNORECASE):
            try:
                await message.delete()
                await message.reply_text(f"{message.from_user.first_name} قسەی ناشرین لەم گروپەدا قەدەغەیە!")
            except Exception:
                pass
            return

    for domain in NSFW_DOMAINS:
        if re.search(domain, text, re.IGNORECASE):
            try:
                await message.delete()
                await message.reply_text(f"{message.from_user.first_name} لینکی نەشیاو قەدەغەیە!")
            except Exception:
                pass
            return

    # AI Reply
    reply = get_ai_reply(message.chat.id, message.from_user.id, text)
    if reply:
        await message.reply_text(reply)

if __name__ == "__main__":
    print("===============================================")
    print("  Zirak Voice Chat Call Music & AI Bot Started!")
    print("===============================================")
    app.run()
