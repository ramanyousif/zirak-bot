# -*- coding: utf-8 -*-
"""
بوتی زیرەک - Telegram Voice Chat Call Music Assistant (Userbot + Bot)
"""

import os
import sys
import re
import json
import random
import asyncio
from pathlib import Path

from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import GroupCallFactory
import yt_dlp
import groq

API_ID = 33605478
API_HASH = "0026515a5d113337a0878ed2e6b1be10"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# Userbot client for Voice Chat streaming
user_app = Client(
    "zirak_userbot_session",
    api_id=API_ID,
    api_hash=API_HASH
)

user_app.send = user_app.invoke

group_call_factory = GroupCallFactory(user_app)
group_call = group_call_factory.get_file_group_call()

groq_client = groq.Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

AI_SYSTEM_PROMPT = """
You are Zirak (زیرەک), a friendly, intelligent young Kurdish guy in a Telegram group chat.
You speak only in short, natural, human Sorani Kurdish (کوردیی سۆرانی ئاسایی چات).

Strict Rules:
1. NEVER translate machine English into Kurdish.
2. Respond in 1 short, natural sentence as a real Kurdish friend in chat.
3. Use everyday Kurdish chat phrases (وەڵا, گیان, کاکە, ئاساییە, عافیەت بێت, هههه).
"""

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

@user_app.on_message(filters.command(["play", "gorani", "music"], prefixes=["/", "."]))
async def play_music_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    query = message.text.split(maxsplit=1)
    
    if len(query) < 2:
        await message.reply_text("تکایە لینکی یوتوب یان ناوی گۆرانییەک بنووسە!\n\nنمونە:\n`/play https://www.youtube.com/watch?v=...`\n`/play شێروان عەبدوڵا`")
        return

    query_str = query[1]
    msg = await message.reply_text("⏳ لەسەر داوای تۆ جۆینی کاڵەکە دەبم و گۆرانییەکە لە ناو کاڵدا پەخش دەکەم... 🎵")

    try:
        file_path, title = await asyncio.to_thread(download_youtube_audio, query_str)
        
        group_call.input_filename = file_path
        if not group_call.is_connected:
            await group_call.start(chat_id)
        
        await msg.edit_text(f"🎵 **ئێستا لە ناو کاڵەکەدا (Group Voice Call) پەخش دەبێت:**\n**{title}**\n\nبۆ ڕاگرتن: `/pause` | بۆ دەستپێکردنەوە: `/resume` | بۆ دەرچوون: `/stop`")
    except Exception as e:
        print("Play Error:", e)
        await msg.edit_text(f"ببوورە گیان! کێشەیەک ڕوویدا لە جۆین بوونی کاڵەکە یان داگرتنی گۆرانی: {e}\n\nدڵنیا ببەوە کە کاڵ (Group Voice Call) کراوەتەوە لە گروپەکەدا!")

@user_app.on_message(filters.command(["pause"], prefixes=["/", "."]))
async def pause_cmd(client: Client, message: Message):
    try:
        group_call.pause_playout()
        await message.reply_text("⏸️ گۆرانییەکە لە کاڵەکەدا ڕاوەستا.")
    except Exception as e:
        await message.reply_text(f"کێشەیەک هەیە: {e}")

@user_app.on_message(filters.command(["resume"], prefixes=["/", "."]))
async def resume_cmd(client: Client, message: Message):
    try:
        group_call.resume_playout()
        await message.reply_text("▶️ گۆرانییەکە دەستی پێ کردەوە.")
    except Exception as e:
        await message.reply_text(f"کێشەیەک هەیە: {e}")

@user_app.on_message(filters.command(["stop", "leave"], prefixes=["/", "."]))
async def stop_cmd(client: Client, message: Message):
    try:
        group_call.stop()
        await message.reply_text("⏹️ لە کاڵەکە دەرباز بووم و گۆرانییەکە ڕاوەستا.")
    except Exception as e:
        await message.reply_text(f"کێشەیەک هەیە: {e}")

if __name__ == "__main__":
    print("===============================================")
    print("  Zirak Voice Chat Call Music Assistant Started!")
    print("===============================================")
    user_app.run()
