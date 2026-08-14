# -*- coding: utf-8 -*-
"""
بوتی زیرەک - Zirak Telegram Bot (24/7 Cloud Ready - Flask & Webhook)
"""

import os
import re
import json
import time
import random
import datetime
import threading
import requests
from pathlib import Path
from flask import Flask, request as flask_request

# ═══════════════════════════════════════════════════════════════════════════════
#  پشتیوانی ئۆتۆماتیکی پروکسی PythonAnywhere
# ═══════════════════════════════════════════════════════════════════════════════
IS_PYTHONANYWHERE = os.path.exists("/home/ramanyousif2002") or "PYTHONANYWHERE_DOMAIN" in os.environ
PROXIES = {
    "http": "http://proxy.server:3128",
    "https": "http://proxy.server:3128"
} if IS_PYTHONANYWHERE else None

if IS_PYTHONANYWHERE:
    os.environ["HTTP_PROXY"] = "http://proxy.server:3128"
    os.environ["HTTPS_PROXY"] = "http://proxy.server:3128"
    os.environ["http_proxy"] = "http://proxy.server:3128"
    os.environ["https_proxy"] = "http://proxy.server:3128"

# ═══════════════════════════════════════════════════════════════════════════════
#  ڕێکخستنەکان (Credentials & Configuration)
# ═══════════════════════════════════════════════════════════════════════════════

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or "".join(["8961124694:", "AAG6ywxBI5DekC3wfzYwn-iEfeCuCr0JiS0"])
GROQ_API_KEY = os.environ.get("GROQ_API_KEY") or "".join(["gsk_YYKuEnabgvL5SWtBzNfVWGdyb3", "FYHobdK8H45gxbFnOhHFkCWNZh"])
GROQ_MODEL = "llama-3.3-70b-versatile"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or "".join(["AQ.Ab8RN6KnX9NtDlWXn", "nyHacFd8zsaaufit8VcVurdXp0CQhc90A"])
MAX_WARNINGS = 3
AUTO_MUTE_MINUTES = 60
WEBHOOK_SECRET = "zirak_secret_2024_xyz"
PA_USERNAME = "ramanyousif2002"

API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ═══════════════════════════════════════════════════════════════════════════════
#  داتای سەیڤکراو (State Management)
# ═══════════════════════════════════════════════════════════════════════════════

STATE_FILE = Path("/home/ramanyousif2002/zirak-bot/data/state.json") if IS_PYTHONANYWHERE else Path("data/state.json")
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

DEFAULT_STATE = {
    "warnings": {},
    "ai_history": {},
    "groups": {},
    "sent_quotes": [],
    "last_clock": "",
    "last_prayer": ""
}

if STATE_FILE.exists():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state_data = json.load(f)
    except Exception:
        state_data = dict(DEFAULT_STATE)
else:
    state_data = dict(DEFAULT_STATE)

for key in DEFAULT_STATE:
    if key not in state_data:
        state_data[key] = DEFAULT_STATE[key]

def save_state():
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Save state error: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
#  سیستەمی ژیریی دەستکردی کوردی (Super Intelligent Kurdish AI)
# ═══════════════════════════════════════════════════════════════════════════════

PRIVATE_AI_SYSTEM_PROMPT = """
تۆ ناوت "زیرەک"ە (Zirak Bot). تۆ زیرەکترین و بەتواناترین یاریدەدەری ژیریی دەستکردی کوردییت (Super Intelligent Kurdish AI).
تۆ وەڵامی هەموو جۆرە پرسیارێک بە شێوەیەکی زۆر ورد، زانستی، ڕوون، بەسوود و جوان بە زمانی کوردیی سۆرانی پوخت و پاراو دەدەیتەوە.

ڕێساکانی وەڵامدانەوە:
١. دەتوانیت لە هەموو بوارێکدا وەڵام بدەیتەوە: زانست، تەکنەلۆژیا، مێژوو، ئایین، کۆمپیوتەر و پرۆگرامین، وەرگێڕان، نووسینی نامە و وتار، پەروەردە، بیرکاری، تەندروستی، یان چاتی ئاسایی هاوڕێیانە.
٢. هەمیشە وەڵامەکانت بە کوردیی سۆرانی بنووسە، بەبێ هەڵەی وەرگێڕانی ووشە بە ووشە.
٣. شێوازی قسەکردنت با هاوڕێیانە، بەڕێز و پڕ لە زانیاری بەسوود بێت (کاکە گیان, گوڵم, بەڕێزم).
٤. هەرگیز وەڵامی تەکراری ڕۆبۆتی مەدەرەوە. ئەگەر شتێکت لێ پرسی ڕاستەوخۆ وەڵامی پرسیارەکە بدەرەوە.
"""

GROUP_AI_SYSTEM_PROMPT = """
تۆ "زیرەک"ی، گەنجێکی زۆر زیرەک، قسەخۆش و دڵسۆزیت لەناو گروپی چاتی کوردی لە تیلیگرام.
بە کوردیی سۆرانی ئاسایی، هاوڕێیانە، ڕەوان و کورت (١ بۆ ٢ ڕستە) بەپێی قسەی کەسەکە وەڵام بدەرەوە.
"""

def clean_ai_text(text: str) -> str:
    if not text:
        return ""
    clean = re.sub(r'(?im)^\s*@?[a-zA-Z0-9_]+:\s*', '', text)
    clean = re.sub(r'\([^()\r\n]*\)', '', clean)
    return clean.strip()

def call_ai(system_prompt: str, user_prompt: str, history: list = None, max_tokens: int = 500) -> str:
    """بانگکردنی Google Gemini 3 Flash (کە لەسەر PythonAnywhere بە تەواوی کراوەیە و زۆر خێرا و زیرەکە)"""
    contents = []
    if history:
        for item in history[-6:]:
            role = "model" if item.get("role") == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": item.get("content", "")}]})
    
    contents.append({"role": "user", "parts": [{"text": user_prompt}]})
    
    g_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={GEMINI_API_KEY}"
    g_headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }
    g_payload = {
        "system_instruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": max_tokens
        }
    }
    
    try:
        r = requests.post(g_url, headers=g_headers, json=g_payload, proxies=PROXIES, timeout=12)
        data = r.json()
        if "candidates" in data and len(data["candidates"]) > 0:
            parts = data["candidates"][0].get("content", {}).get("parts", [])
            for p in parts:
                if "text" in p and p["text"]:
                    return clean_ai_text(p["text"])
    except Exception as e:
        print("Gemini API Error in call_ai:", e)

    return None

SMART_REPLIES = [
    {
        "patterns": ["سڵاو", "سلاو", "سلام", "هەڵۆ", "hello", "hi"],
        "replies": ["سڵاو لە تۆش گیان! ❤️ چۆنیت؟", "سڵاو بەخێر بێیت گوڵم! 🌸", "سڵاو و ڕێز بۆ تۆی ئازیز 💖"]
    },
    {
        "patterns": ["چۆنیت", "چونیت", "چۆنی", "چاکیت", "باشیت", "چ هەواڵ"],
        "replies": ["سوپاس بۆ خودا من زۆر باشم، تۆ چۆنیت گیان؟ ✨", "زۆر باشم سوپاس! چی دەکەیت؟ 😊", "سوپاس گەورەم، من باشم تۆ چۆنیت؟ ❤️"]
    },
    {
        "patterns": ["دەستت خۆش", "دەست خۆش", "دەستت کەڵەک پێ بێت", "دەستت ڕەنگین"],
        "replies": ["عافیەتت بێت گیانەکەم! ❤️", "سەرکەوتوو بیت، شایەنی نییە 🌸", "دەستی تۆش خۆش بێت گوڵم ✨"]
    },
    {
        "patterns": ["ناوی تۆ چییە", "ناوت چییە", "تۆ کێیت", "کێیت"],
        "replies": ["من ناوم زیرەکە! هاوڕێ و ژیریی دەستکردی دڵسۆزی کوردم 🤖❤️", "من زیرەکم! خزمەتکاری ئێوەی ئازیز 🌸"]
    }
]

def get_smart_reply(text: str):
    lower = text.strip().lower()
    for entry in SMART_REPLIES:
        for p in entry["patterns"]:
            if p == lower or (len(p) > 3 and p in lower):
                return random.choice(entry["replies"])
    return None

def get_ai_reply(chat_id: int, user_id: int, question: str, is_private: bool = False) -> str:
    smart = get_smart_reply(question)
    if smart:
        return smart

    system_prompt = PRIVATE_AI_SYSTEM_PROMPT if is_private else GROUP_AI_SYSTEM_PROMPT
    max_tokens = 700 if is_private else 150

    u_key = str(user_id)
    history = state_data["ai_history"].get(u_key, []) if is_private else []

    answer = call_ai(system_prompt, question, history=history, max_tokens=max_tokens)
    if answer:
        if is_private:
            history.append({"role": "user", "content": question})
            history.append({"role": "assistant", "content": answer})
            state_data["ai_history"][u_key] = history[-8:]
            save_state()
        return answer

    if is_private:
        return "ببوورە گیان کەمێک کێشەی هێڵ هەیە، تکایە جارێکی تر پرسیارەکەت بنووسەوە! 🌸"
    return None

# ═══════════════════════════════════════════════════════════════════════════════
#  وتەکانی کاتژمێری و زیکر
# ═══════════════════════════════════════════════════════════════════════════════

FALLBACK_QUOTES = [
    "مرۆڤ بە ڕەوشت و زانستەکەی گەورەیە، نەک بە سامانەکەی.",
    "هەرگیز ئومێد لەدەست مەدە، تاریكترین ساتەکانی شەو بەرهەمی سپێدەی ڕۆژێکی ڕووناکە.",
    "گەورەترین سەرمایەی مرۆڤ کاتە، بە شتی بەسوود بەسەری ببە.",
    "دڵخۆشی بەخشین بە دەوروبەرت، خۆشبەختیت بۆ دەگەڕێنێتەوە.",
    "وتەی جوان و زەردەخەنەیەک دەتوانێت دڵی هەزاران کەس بکاتەوە.",
    "سەرکەوتن بەرهەمی کۆڵنەدان و هەوڵدانی بەردەوامە.",
    "بە باشی ڕوانین بۆ ئایندە، هەنگاوی یەکەمی سەرکەوتنە.",
    "لە هەموو بارودۆخێکدا سوپاسگوزاری پەروەردگار بە.",
    "ژیان وەک ئاوێنەیە، ئەگەر لێی خەندە بکەیت، ئەویش خەندەت بۆ دەکاتەوە.",
    "گەورەیی لەوەدا نییە کە هەرگیز نەکەویت، بەڵکو لەوەدایە دوای هەر کەوتنێک هەستیتەوە.",
    "باوەڕت بە خۆت هەبێت، چونکە تۆ دەتوانیت شتە مەزنەکان ئەنجام بدەیت.",
    "ئەو کەسەی دەیەوێت بگاتە لوتکە، نابێت لە ماندووبوون بترسێت.",
    "هەموو ڕۆژێک هەلێکی نوێیە بۆ باشتربوون.",
    "زانست تاکە سامانێکە کە بە بەخشین زیاد دەکات.",
    "لێبوردەیی نیشانەی هێزە، نەک بێهێزی.",
    "سادەیی جوانترین جۆری پێشکەوتنە.",
    "ڕۆژانە هەوڵبدە ببیتە هۆکاری خەندەی کەسێک.",
    "بیرکردنەوەی ئەرێنی، کلیلی دەرگا داخراوەکانە.",
    "هەڵەکانمان وانەی ژیانن، نەک کۆتایی ڕێگاکە.",
    "چاکە بکە و لەبیری بکە، ڕۆژێک دێت بەری دەبینیت.",
    "بەختەوەری لە ناخەوە هەڵدەقوڵێت، نەک لە دەوروبەرەوە.",
    "ئارامگرتن تاڵە، بەڵام بەرهەمەکەی شیرینە.",
    "ڕێزگرتن لە بەرامبەر، ڕێزگرتنە لە خودی خۆت.",
    "وشەی جوان وەک بارانی بەهارە، ڕۆح دەژێنێتەوە.",
    "هەنگاوی بچووک بەردەوام، باشترە لە هەنگاوی گەورەی پچڕ پچڕ.",
    "کاتە سەختەکان کەسە بەهێزەکان دروست دەکەن.",
    "ڕاستگۆیی گەورەترین سەرمایەی مرۆڤە.",
    "ژیان کورتە، بە سادەیی و جوانی بژی.",
    "گەورەترین سەرکەوتن ئەوەیە کە زاڵ بیت بەسەر ناخی خۆتدا.",
    "هیوا تاکە چرایەکە کە لە تاریکیدا ڕووناکی دەدات."
]

def generate_unique_quote():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))
    time_context = "شەو" if (now.hour >= 21 or now.hour < 5) else ("بەیانی" if now.hour < 12 else "پاشنیوەڕۆ")
    
    prompt = f"تۆ شاعیرێکی کوردیی سۆرانیت. تەنها یەک وتەی کورت، جوان، پڕمانا و زۆر قەشەنگ بۆ کاتی {time_context} بنووسە. تەنها دەقی وتەکە بنووسە بەبێ هیچ ڕوونکردنەوەیەک."
    ans = call_ai("تەنها یەک وتەی کوردیی سۆرانی کورت بنووسە.", prompt, max_tokens=100)
    if ans and len(ans) > 6:
        ans = ans.replace('"', '').replace("'", "").strip()
        ans = re.sub(r'^[\-\*\d\.\)]+\s*', '', ans).strip()
        return ans

    sent = state_data.get("sent_quotes", [])
    available = [q for q in FALLBACK_QUOTES if q not in sent]
    if not available:
        state_data["sent_quotes"] = []
        available = list(FALLBACK_QUOTES)

    chosen = random.choice(available)
    state_data["sent_quotes"].append(chosen)
    save_state()
    return chosen

PRAYER_MESSAGES = {
    "Fajr": "🕌 *کاتی نوێژی بەیانییە (فەجر)* 🌸\n\n﴿إِنَّ قُرْآنَ الْفَجْرِ كَانَ مَشْهُودًا﴾\nسەڵاوات لەسەر پێغەمبەری خوا (ﷺ) لێبدەن: أللَّهُمَّ صَلِّ عَلَى مُحَمَّدٍ وَعَلَى آلِ مُحَمَّدٍ 🤍",
    "Dhuhr": "🕌 *کاتی نوێژی نیوەڕۆیە (ژوهر)* 🌸\n\nزیکری پیرۆز: سُبْحَانَ اللَّهِ وَبِحَمْدِهِ ، سُبْحَانَ اللَّهِ الْعَظِيمِ ✨",
    "Asr": "🕌 *کاتی نوێژی عەسردایە* 🌸\n\nزیکری پیرۆز: لا إِلَهَ إِلا اللَّهُ وَحْدَهُ لا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ 🌿",
    "Maghrib": "🕌 *کاتی نوێژی ئێوارەیە (مەغریب)* 🌸\n\nزیکری پیرۆز: أَسْتَغْفِرُ اللَّهَ وَأَتُوبُ إِلَيْهِ 💐",
    "Isha": "🕌 *کاتی نوێژی عیشایە (خەوتنان)* 🌸\n\nزیکری پیرۆز: لا حَوْلَ وَلا قُوَّةَ إِلا بِاللَّهِ الْعَلِيِّ الْعَظِيمِ 🌟"
}

LIVE_PRAYER_TIMES = {
    "Fajr": "03:37",
    "Dhuhr": "12:10",
    "Asr": "15:57",
    "Maghrib": "19:05",
    "Isha": "20:36"
}

LAST_API_FETCH_DAY = ""

def fetch_live_prayer_times():
    global LIVE_PRAYER_TIMES, LAST_API_FETCH_DAY
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    if LAST_API_FETCH_DAY == today_str:
        return
    try:
        r = requests.get("http://api.aladhan.com/v1/timingsByCity?city=Erbil&country=Iraq&method=3", proxies=PROXIES, timeout=10)
        data = r.json()
        if data and data.get("code") == 200:
            timings = data["data"]["timings"]
            for key in ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]:
                val = timings.get(key, "")
                if val:
                    LIVE_PRAYER_TIMES[key] = val.split(" ")[0]
            LAST_API_FETCH_DAY = today_str
    except Exception as e:
        print(f"Aladhan API fetch exception: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
#  فیلتەری وشەی ناشرین و لینک
# ═══════════════════════════════════════════════════════════════════════════════

STANDALONE_BAD_WORDS = ['قن', 'گو', 'کیر', 'کێر', 'تڕ']

EXPLICIT_BAD_WORDS = [
    'قنت', 'قنم', 'قنی', 'قوز', 'قۆز', 'قوزت', 'قوزم', 'قوزی',
    'کێرم', 'کیرم', 'کێری', 'کێرت', 'کیرت',
    'گواو', 'گوخۆر', 'گوو', 'گو', 'گوت', 'گووم', 'گواوی',
    'حیز', 'سۆزانی', 'سێکس', 'پۆرن', 'قەحبە', 'گەواد', 'پینتی', 'بێنامووس',
    'ئەتگێم', 'ئەگێم', 'بگێم', 'بگێرم', 'تێبگێم', 'گاین', 'تێگەین', 'بگێین', 'داپێنم',
    'fuck', 'shit', 'bitch', 'asshole', 'dick', 'pussy',
    'bastard', 'whore', 'slut', 'nigger', 'faggot', 'cock', 'cunt',
    'motherf', 'stfu', 'porn', 'xxx', 'nude', 'naked',
    'boobs', 'tits', 'penis', 'vagina', 'orgasm', 'hentai'
]

BAD_PHRASES_LIST = [
    r'لە\s*دایکت', r'دایکت\s*بگێم', r'دایکت\s*گێم', r'دایکت\s*بێ', r'دایکت\s*بم', r'دایکت\s*بکێم',
    r'لە\s*خوشکت', r'خوشکت\s*بگێم', r'خوشکت\s*گێم', r'خوشکت\s*بێ', r'خوشکت\s*بم', r'خوشکت\s*بکێم',
    r'لە\s*عەرزت', r'لە\s*قەبرت', r'داپیرەت\s*بم', r'بێ\s*دایک', r'بێ\s*خوشک', r'سەر\s*قن', r'کێرم\s*لە',
    r'لە\s*قنت', r'لە\s*قنم', r'لە\s*قنی', r'لە\s*قوزت', r'لە\s*قوزم'
]

def normalize_kurdish(text: str) -> str:
    if not text:
        return ""
    t = text.replace("ك", "ک").replace("ي", "ی").replace("ى", "ی").replace("ئـ", "ئ")
    t = re.sub(r'[\u200b\u200c\u200d\u200e\u200f\ufeff]+', ' ', t)
    t = re.sub(r'\s+', ' ', t)
    return t.strip().lower()

def contains_bad_word(text: str) -> bool:
    if not text:
        return False
    norm = normalize_kurdish(text)
    words = norm.split()

    for w in words:
        if w in STANDALONE_BAD_WORDS:
            return True
    for w in EXPLICIT_BAD_WORDS:
        if w in norm:
            return True
    for phrase in BAD_PHRASES_LIST:
        if re.search(phrase, norm, re.IGNORECASE):
            return True
    return False

def contains_link_or_spam(msg: dict, text: str) -> bool:
    if text and re.search(r'(?i)\bhttps?://|\bt\.me/|\btelegram\.me/|\bwww\.', text):
        return True
    if msg.get("entities"):
        for e in msg["entities"]:
            if e.get("type") in ["url", "text_link"]:
                return True
    if msg.get("caption_entities"):
        for e in msg["caption_entities"]:
            if e.get("type") in ["url", "text_link"]:
                return True
    if msg.get("reply_markup"):
        return True
    return False

# ───── فلتەری توندی ستیکەر و گیف و میدیای نەشیاو و +18 ─────
NSFW_KEYWORDS = [
    'porn', 'porno', 'sex', 'sexy', 'nsfw', 'xxx', 'hentai', 'nude', 'naked', 'erotic', 'adult',
    'boobs', 'tits', 'dick', 'pussy', 'cock', 'cunt', 'milf', 'anal', 'vagina', 'penis',
    'lust', 'horny', 'sensual', 'fetish', 'bdsm', 'blowjob', 'ass', 'butt', 'dildo',
    '18plus', 'plus18', 'badgirl', 'badboy', 'lewd', 'ecchi', 'rule34', 'yiff', 'orgasm',
    'cum', 'sperm', 'hardcore', 'softcore', 'strip', 'stripper', 'penetration', 'uncensored',
    'gangbang', 'creampie', 'squirt', 'deepthroat', 'masturbat', 'boobies', 'nipples', 'thong',
    'teenfidelity', 'brazzers', 'pornhub', 'xhamster', 'xvideos', 'onlyfans', 'fap', 'tushy',
    'vixen', 'blacked', 'sweeties', 'redgifs', 'spankbang', 'eporner', 'fakku', 'erome',
    'manyvids', 'chaturbate', 'cam4', 'bongacams', 'camsoda', 'stripchat', 'livejasmin',
    'naughty', 'dirty', 'erotica', 'kinky', 'nakedgirl', 'nakedboy', 'slut', 'whore',
    'سێکس', 'سێکسی', 'پۆرن', 'ڕووت', 'قوز', 'قۆز', 'کێر', 'کیر', 'حیز', 'سۆزانی',
    'قەحبە', 'گەواد', 'گاین', 'داپێنم', 'پینتی', 'گوان', 'مەمک', 'قن', 'کۆم', '18+', '+18',
    'sex', 'hot', 'girls', 'boob', 'ass'
]

GEMINI_API_KEY = "".join(["AQ.Ab8RN6KnX9NtDlWXn", "nyHacFd8zsaaufit8VcVurdXp0CQhc90A"])

def check_media_nsfw_gemini(file_id: str) -> bool:
    """
    Visual AI check for Stickers, GIFs, and Photos using Google Gemini Vision (Whitelisted on PythonAnywhere)
    """
    if not file_id:
        return False
    try:
        file_info = tg_call("getFile", {"file_id": file_id})
        if not file_info or not file_info.get("ok"):
            return False
        file_path = file_info["result"].get("file_path", "")
        if not file_path or file_path.endswith(".tgs"):
            return False

        img_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        img_res = requests.get(img_url, proxies=PROXIES, timeout=8)
        if img_res.status_code != 200 or not img_res.content:
            return False

        import io
        import base64
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(img_res.content)).convert("RGB")
            img.thumbnail((300, 300))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=80)
            b64_img = base64.b64encode(buf.getvalue()).decode("utf-8")
        except Exception:
            b64_img = base64.b64encode(img_res.content).decode("utf-8")

        g_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={GEMINI_API_KEY}"
        g_headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY
        }
        g_payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": "Is this image or sticker or GIF pornographic, depicting explicit nudity, sexual intercourse, exposed genitals, or adult +18 NSFW content? Answer with ONLY 'YES' or 'NO'."
                        },
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": b64_img
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 300
            }
        }
        r = requests.post(g_url, headers=g_headers, json=g_payload, proxies=PROXIES, timeout=10)
        res_data = r.json()
        if "candidates" in res_data and len(res_data["candidates"]) > 0:
            parts = res_data["candidates"][0].get("content", {}).get("parts", [])
            for p in parts:
                txt = p.get("text", "").strip().upper()
                if "YES" in txt:
                    print("🚨 Sexy / NSFW media detected by Google Gemini Vision AI!")
                    return True
                elif "NO" in txt:
                    return False
    except Exception as e:
        print(f"Gemini Vision check exception: {e}")
    return False

check_sticker_nsfw_gemini = check_media_nsfw_gemini

NSFW_PACKS_CACHE = set()
SAFE_PACKS_CACHE = set()

def is_nsfw_media_gemini(msg: dict) -> tuple:
    """
    Intelligent visual filter for stickers and GIFs via Google Gemini Vision AI
    """
    thumb_id = None

    if "sticker" in msg:
        st = msg["sticker"]
        emoji = st.get("emoji") or ""
        
        if "🔞" in emoji:
            return True, "ناردنی ستیکەری نەشیاو و +18 🔞"

        set_name = (st.get("set_name") or "").lower()
        if set_name:
            if set_name in NSFW_PACKS_CACHE:
                return True, "ناردنی ستیکەری سێکسی و +18 🔞"
                
            norm_set = normalize_kurdish(set_name.replace('_', ' ').replace('-', ' ').replace('.', ' '))
            for kw in NSFW_KEYWORDS:
                if kw in set_name or kw in norm_set:
                    NSFW_PACKS_CACHE.add(set_name)
                    return True, "ناردنی ستیکەری سێکسی و +18 🔞"
            if contains_bad_word(norm_set):
                NSFW_PACKS_CACHE.add(set_name)
                return True, "ناردنی ستیکەری نەشیاو 🔞"

            try:
                res = tg_call("getStickerSet", {"name": set_name})
                if res and res.get("ok"):
                    title = (res["result"].get("title") or "").lower()
                    norm_title = normalize_kurdish(title.replace('_', ' ').replace('-', ' ').replace('.', ' '))
                    for kw in NSFW_KEYWORDS:
                        if kw in title or kw in norm_title:
                            NSFW_PACKS_CACHE.add(set_name)
                            return True, "ناردنی ستیکەری سێکسی و +18 🔞"
                    if contains_bad_word(norm_title):
                        NSFW_PACKS_CACHE.add(set_name)
                        return True, "ناردنی ستیکەری نەشیاو 🔞"
            except Exception:
                pass

        if st.get("thumbnail"):
            thumb_id = st["thumbnail"].get("file_id")
        elif not st.get("is_video") and not st.get("is_animated"):
            thumb_id = st.get("file_id")
        elif st.get("is_video"):
            thumb_id = st.get("thumbnail", {}).get("file_id") or st.get("file_id")

    if "animation" in msg:
        anim = msg["animation"]
        f_name = (anim.get("file_name") or "").lower()
        if f_name:
            norm_fn = normalize_kurdish(f_name.replace('_', ' ').replace('-', ' ').replace('.', ' '))
            for kw in NSFW_KEYWORDS:
                if kw in f_name or kw in norm_fn:
                    return True, "ناردنی گیفی نەشیاو و +18 🔞"
            if contains_bad_word(norm_fn):
                return True, "ناردنی گیفی نەشیاو 🔞"
        thumb_id = anim.get("thumbnail", {}).get("file_id") or anim.get("file_id")

    doc = msg.get("document") or msg.get("video") or {}
    if doc and not thumb_id:
        f_name = (doc.get("file_name") or "").lower()
        if f_name:
            norm_fn = normalize_kurdish(f_name.replace('_', ' ').replace('-', ' ').replace('.', ' '))
            for kw in NSFW_KEYWORDS:
                if kw in f_name or kw in norm_fn:
                    return True, "ناردنی میدیای نەشیاو 🔞"
            if contains_bad_word(norm_fn):
                return True, "ناردنی میدیای نەشیاو 🔞"
        thumb_id = doc.get("thumbnail", {}).get("file_id") or doc.get("file_id")

    if "photo" in msg and msg["photo"] and not thumb_id:
        thumb_id = msg["photo"][-1].get("file_id")

    if thumb_id:
        if check_media_nsfw_gemini(thumb_id):
            return True, "ناردنی ستیکەر یان گیفی سێکسی و +18 🔞"

    return False, ""

is_sticker_blocked = is_nsfw_media_gemini

def is_forwarded_message(msg: dict) -> bool:
    """پشکنینی ئەوەی ئایا پەیامەکە فۆڕوەرد (Forward) کراوە لە کەناڵ یان چاتی تر"""
    return any(k in msg for k in [
        "forward_date", "forward_from", "forward_from_chat", 
        "forward_sender_name", "forward_origin", "forward_from_message_id"
    ])

# ═══════════════════════════════════════════════════════════════════════════════
#  فەنکشنەکانی تیلیگرام
# ═══════════════════════════════════════════════════════════════════════════════

def tg_call(method: str, payload: dict = None):
    try:
        r = requests.post(f"{API_BASE}/{method}", json=payload or {}, proxies=PROXIES, timeout=30)
        return r.json()
    except Exception as e:
        print(f"Telegram API Error ({method}): {e}")
        return None

BOT_ID = 0
me_data = tg_call("getMe")
if me_data and me_data.get("ok"):
    BOT_ID = me_data["result"]["id"]

def send_message(chat_id: int, text: str, reply_to: int = 0):
    body = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True, "parse_mode": "Markdown"}
    if reply_to > 0:
        body["reply_to_message_id"] = reply_to
        body["allow_sending_without_reply"] = True
    res = tg_call("sendMessage", body)
    if res and not res.get("ok"):
        body.pop("parse_mode", None)
        tg_call("sendMessage", body)

def delete_message(chat_id: int, message_id: int):
    tg_call("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

def get_display_name(user_obj: dict) -> str:
    if not user_obj:
        return "?"
    if user_obj.get("first_name"):
        return user_obj["first_name"]
    if user_obj.get("username"):
        return f"@{user_obj['username']}"
    return str(user_obj.get("id", "?"))

def is_admin(chat_id: int, user_id: int) -> bool:
    res = tg_call("getChatMember", {"chat_id": chat_id, "user_id": user_id})
    if res and res.get("ok"):
        return res["result"]["status"] in ["creator", "administrator"]
    return False

def add_user_warning(chat_id: int, user_id: int) -> int:
    c_key = str(chat_id)
    u_key = str(user_id)
    if c_key not in state_data["warnings"]:
        state_data["warnings"][c_key] = {}
    current = state_data["warnings"][c_key].get(u_key, 0) + 1
    state_data["warnings"][c_key][u_key] = current
    save_state()
    return current

def set_user_mute(chat_id: int, user_id: int, minutes: int = 60):
    until = int(time.time()) + (minutes * 60)
    tg_call("restrictChatMember", {
        "chat_id": chat_id,
        "user_id": user_id,
        "until_date": until,
        "permissions": {
            "can_send_messages": False,
            "can_send_media_messages": False,
            "can_send_other_messages": False,
            "can_add_web_page_previews": False
        }
    })

def broadcast_to_groups(text: str):
    if not text:
        return
    groups = state_data.get("groups", {})
    for g_id_str in list(groups.keys()):
        try:
            send_message(int(g_id_str), text)
        except Exception as e:
            print(f"Broadcast error for {g_id_str}: {e}")

WELCOME_MESSAGES = [
    "🌸 سڵاو {name} گیان! زۆر بەخێر هاتیت بۆ گروپەکەمان 🎉\n\nگەرمترین بەخێرهاتنت لێ دەکەین، هیوادارین کاتێکی زۆر خۆش و بەسوود لەگەڵمان بەسەر ببەیت! ✨❤️",
    "👑 سڵاو لە {name} خۆشەویست! زۆر بەخێربێیت بۆ نێو خێزانە چاک و ئازیزەکەمان 🌟\n\nخۆشحاڵین بە هاتنت، بە هیوای کاتی خۆش و سەرکەوتووانە! 🌺",
    "✨ سڵاو و دەرەکەت خۆش {name} گیان! بەخێربێیت بەسەر چاوانمان 💐\n\nگروپ بە هاتنی تۆ ڕووناک بووەوە! 🎉"
]

# ═══════════════════════════════════════════════════════════════════════════════
#  سیستەمی قوفڵی ئەتۆمی بۆ ڕێگریکردن لە دووبارەبوونەوە (Atomic Schedule Lock)
# ═══════════════════════════════════════════════════════════════════════════════

LOCK_DIR = Path("/home/ramanyousif2002/zirak-bot/data/locks") if IS_PYTHONANYWHERE else Path("data/locks")

def claim_schedule_lock(lock_name: str, stamp: str) -> bool:
    """
    سەرکەوتووانە دەست بەسەر ئەم کاتژمێرە یان نوێژەدا دەگرێت
    ڕێگە نادات هیچ کاتژمێر یان زیکرێک زیاتر لە ١ جار بنێردرێت
    تەنانەت ئەگەر چەندین پڕۆسەی سێرڤەر بە یەکەوە کار بکەن
    """
    try:
        LOCK_DIR.mkdir(parents=True, exist_ok=True)
        safe_stamp = re.sub(r'[^a-zA-Z0-9_\-]', '_', stamp)
        lock_file = LOCK_DIR / f"{lock_name}_{safe_stamp}.lock"
        
        # Atomic lock creation at OS level (تەنها ١ پڕۆسە دەتوانێت ئەم فایلە دروست بکات)
        fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, 'w') as f:
            f.write(str(time.time()))
        
        # پاککردنەوەی فایلە کۆنەکانی پێشتر (زیاتر لە ٣ کاتژمێر)
        try:
            now_ts = time.time()
            for old_f in LOCK_DIR.glob("*.lock"):
                if now_ts - old_f.stat().st_mtime > 10800:
                    old_f.unlink(missing_ok=True)
        except Exception:
            pass

        return True
    except FileExistsError:
        return False
    except Exception as e:
        print(f"Schedule lock error: {e}")
        return False

# ═══════════════════════════════════════════════════════════════════════════════
#  پشکنینی کاتژمێرە هاوشێوەکان و نوێژەکان (تەنها ١ جار بە تەواوەتی)
# ═══════════════════════════════════════════════════════════════════════════════

def check_scheduled_tasks():
    # Kurdistan Timezone (UTC+3)
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))
    current_time_str = now.strftime("%H:%M")
    current_stamp_str = now.strftime("%Y-%m-%d %H:%M")

    # Mirror times: 1:01, 2:02, 3:03 ... 11:11, 12:12, 13:01 ... 23:11
    h12 = now.hour % 12
    if h12 == 0:
        h12 = 12

    is_matching_time = (now.minute == h12)

    # ١. کاتژمێری هاوشێوە + یەک وتەی نوێ (تەنها ١ جار بە تەواوەتی)
    if is_matching_time:
        if claim_schedule_lock("clock", current_stamp_str):
            period = "شەو" if (now.hour >= 21 or now.hour < 5) else ("بەیانی" if now.hour < 12 else "پاشنیوەڕۆ")
            digits_kurdish = {"0":"۰", "1":"۱", "2":"۲", "3":"۳", "4":"٤", "5":"٥", "6":"٦", "7":"٧", "8":"٨", "9":"٩"}
            k_hour = "".join([digits_kurdish.get(c, c) for c in str(h12)])
            k_min = "".join([digits_kurdish.get(c, c) for c in f"{now.minute:02d}"])

            quote = generate_unique_quote()
            clock_msg = f"🕐 *کاتژمێر {k_hour}:{k_min} ی {period}ە* ✨\n\n✨ *وتەی کاتژمێر:*\n{quote}"
            broadcast_to_groups(clock_msg)

    # ٢. کاتی نوێژەکان و زیکر (تەنها ١ جار بە تەواوەتی)
    fetch_live_prayer_times()
    for prayer_name, prayer_time in LIVE_PRAYER_TIMES.items():
        if current_time_str == prayer_time:
            p_check_key = f"{now.strftime('%Y-%m-%d')}_{prayer_name}"
            if claim_schedule_lock("prayer", p_check_key):
                prayer_msg = PRAYER_MESSAGES.get(prayer_name, "")
                if prayer_msg:
                    broadcast_to_groups(prayer_msg)

# ═══════════════════════════════════════════════════════════════════════════════
#  بەڕێوەبردنی پەیامەکان
# ═══════════════════════════════════════════════════════════════════════════════

def handle_message(msg: dict):
    if not msg or "chat" not in msg:
        return

    chat = msg["chat"]
    chat_type = chat["type"]
    if chat_type not in ["group", "supergroup", "private"]:
        return

    chat_id = chat["id"]
    msg_id = msg.get("message_id", 0)

    # تۆمارکردنی گروپەکە
    if chat_type in ["group", "supergroup"]:
        g_key = str(chat_id)
        if g_key not in state_data["groups"]:
            state_data["groups"][g_key] = True
            save_state()

    # 🌸 بەخێرهاتنی ئەندامانی نوێ
    new_members = []
    if "new_chat_members" in msg and msg["new_chat_members"]:
        new_members.extend(msg["new_chat_members"])
    if "new_chat_participant" in msg and msg["new_chat_participant"]:
        new_members.append(msg["new_chat_participant"])
    if "new_chat_member" in msg and msg["new_chat_member"]:
        new_members.append(msg["new_chat_member"])

    seen_ids = set()
    for member in new_members:
        if isinstance(member, dict):
            m_id = member.get("id")
            if m_id and m_id not in seen_ids:
                seen_ids.add(m_id)
                if not member.get("is_bot"):
                    m_name = get_display_name(member)
                    w_msg = random.choice(WELCOME_MESSAGES).format(name=m_name)
                    send_message(chat_id, w_msg, reply_to=0)

    if "from" not in msg or not msg["from"]:
        return

    from_user = msg["from"]
    user_id = from_user["id"]
    display_name = get_display_name(from_user)
    text = msg.get("text") or msg.get("caption") or ""

    # 💬 ۱. چاتی شەخسی (Smart Kurdish AI Assistant)
    if chat_type == "private":
        if text:
            reply = get_ai_reply(chat_id, user_id, text, is_private=True)
            if reply:
                send_message(chat_id, reply, msg_id)
        return

    # 🛡️ ۲. ئاسایشی توندی گروپ (سڕینەوەی دەستبەجێی ستیکەر، گیف، فۆڕوەرد، لینک و جنێو بۆ ئەندامان)
    is_user_admin = is_admin(chat_id, user_id)

    if not is_user_admin:
        violation = ""

        # ١. ستیکەر (هەموو جۆرە ستیکەرێک بۆ ئەندامان قەدەغەیە تا هیچ شتێکی نەشیاو نەیەتە ناو گروپ)
        if "sticker" in msg:
            violation = "ناردنی ستیکەر 🚫"

        # ٢. گیف (GIF)
        elif "animation" in msg:
            violation = "ناردنی گیف (GIF) 🚫"

        # ٣. فۆڕوەرد لە کەناڵ یان چاتی تر
        elif is_forwarded_message(msg):
            violation = "ناردنی فۆڕوەرد (Forward) لە کەناڵ یان چاتی تر 🔗"

        # ٤. لینک و ڕیکلام
        elif contains_link_or_spam(msg, text):
            violation = "ناردنی لینک یان ریکلام 🔗"

        # ٥. قسەی ناشرین و جنێو
        elif contains_bad_word(text):
            violation = "قسەی ناشرین 🤬"

        # ٦. ڤیدیۆی بێ نووسین
        elif "video" in msg and not text:
            violation = "ناردنی ڤیدیۆ بەبێ نووسین 🎥"

        if violation:
            delete_message(chat_id, msg_id)
            cnt = add_user_warning(chat_id, user_id)
            send_message(chat_id, f"⚠️ {display_name} {violation} قەدەغەیە! ئاگاداری: ({cnt}/{MAX_WARNINGS})")
            if cnt >= MAX_WARNINGS:
                set_user_mute(chat_id, user_id, AUTO_MUTE_MINUTES)
                send_message(chat_id, f"🚫 {display_name} بەهۆی دووبارەکردنەوەی سەرپێچی، بۆ ماوەی ١ کاتژمێر لە چاتکردن بێدەنگ کرا!")
            return

    # 💬 ۳. وەڵامدانەوەی AI لە گروپدا (ئەگەر دوو کەس قسە لەگەڵ یەکتر بکەن، بووت بێدەنگ دەبێت)
    if text:
        if "reply_to_message" in msg and msg["reply_to_message"]:
            target_user = msg["reply_to_message"].get("from", {})
            target_id = target_user.get("id", 0)
            is_target_bot = target_user.get("is_bot", False)
            if target_id != BOT_ID and not is_target_bot:
                return  # دوو مرۆڤن قسەیان لەگەڵ یەکە، بووت بێدەنگ دەمێنێت

        reply = get_ai_reply(chat_id, user_id, text, is_private=False)
        if reply:
            send_message(chat_id, reply, msg_id)

# ═══════════════════════════════════════════════════════════════════════════════
#  Flask Webhook App
# ═══════════════════════════════════════════════════════════════════════════════

app = Flask(__name__)

# سڕینەوەی کێشەی شەدوولەر بە دروستکردنی Background Worker ی بێ کێشە
_scheduler_started = False
def init_scheduler():
    global _scheduler_started
    if not _scheduler_started:
        _scheduler_started = True
        def _loop():
            time.sleep(5)
            while True:
                try:
                    check_scheduled_tasks()
                except Exception as e:
                    print("Scheduler Loop Error:", e)
                time.sleep(25)
        t = threading.Thread(target=_loop, daemon=True)
        t.start()
        print("✅ Background 24/7 Scheduler Started Successfully!")

init_scheduler()

@app.route("/")
def home():
    return "🤖 Zirak Bot is alive! ✨", 200

@app.route(f"/{WEBHOOK_SECRET}", methods=["POST"])
def webhook():
    try:
        data = flask_request.get_json(force=True)
        if data:
            if "message" in data:
                handle_message(data["message"])
            if "chat_member" in data:
                cm = data["chat_member"]
                new_st = cm.get("new_chat_member", {}).get("status")
                old_st = cm.get("old_chat_member", {}).get("status")
                if new_st == "member" and old_st in ["left", "kicked", "restricted", None]:
                    c_id = cm.get("chat", {}).get("id")
                    u_info = cm.get("new_chat_member", {}).get("user", {})
                    if c_id and u_info and not u_info.get("is_bot"):
                        m_name = get_display_name(u_info)
                        w_msg = random.choice(WELCOME_MESSAGES).format(name=m_name)
                        send_message(c_id, w_msg)
    except Exception as e:
        print(f"Webhook error: {e}")
    return "OK", 200

@app.route("/cron", methods=["GET"])
def cron_endpoint():
    try:
        check_scheduled_tasks()
        return "Cron OK", 200
    except Exception as e:
        return f"Cron Error: {e}", 500

@app.route("/set_webhook", methods=["GET"])
def set_webhook():
    webhook_url = f"https://{PA_USERNAME}.pythonanywhere.com/{WEBHOOK_SECRET}"
    result = tg_call("setWebhook", {
        "url": webhook_url,
        "allowed_updates": ["message", "chat_member"]
    })
    return f"Webhook set result: {result}", 200

# ═══════════════════════════════════════════════════════════════════════════════
#  Long Polling Engine (بۆ ڕەنکردنی لۆکاڵ یان لە کۆنسۆڵ)
# ═══════════════════════════════════════════════════════════════════════════════

def main_polling():
    tg_call("deleteWebhook", {"drop_pending_updates": True})
    print("===============================================")
    print("  Zirak Bot - Continuous 24/7 Engine")
    print("===============================================")

    offset = 0
    while True:
        try:
            try:
                check_scheduled_tasks()
            except Exception as e:
                print("Scheduled task error:", e)

            res = tg_call("getUpdates", {"offset": offset, "timeout": 5})
            if res and res.get("ok"):
                for update in res["result"]:
                    offset = update["update_id"] + 1
                    if "message" in update:
                        handle_message(update["message"])
        except Exception as e:
            print("Loop Exception:", e)
            time.sleep(5)

if __name__ == "__main__":
    main_polling()
