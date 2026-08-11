# -*- coding: utf-8 -*-
"""
بوتی زیرەک - Zirak Telegram Security & AI Bot (24/7 Cloud Ready)
"""

import os
import re
import json
import time
import random
import datetime
import requests
from pathlib import Path
import groq

# ═══════════════════════════════════════════════════════════════════════════════
#  پشتیوانی ئۆتۆماتیکی پروکسی PythonAnywhere
# ═══════════════════════════════════════════════════════════════════════════════
if os.path.exists("/home/ramanyousif2002") or "PYTHONANYWHERE_DOMAIN" in os.environ:
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
MAX_WARNINGS = 3
AUTO_MUTE_MINUTES = 60

API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"
groq_client = groq.Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

STATE_FILE = Path("data/state.json")
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

if STATE_FILE.exists():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state_data = json.load(f)
    except Exception:
        state_data = {"warnings": {}, "ai_history": {}, "groups": {}, "sent_quotes": []}
else:
    state_data = {"warnings": {}, "ai_history": {}, "groups": {}, "sent_quotes": []}

if "groups" not in state_data:
    state_data["groups"] = {}
if "sent_quotes" not in state_data:
    state_data["sent_quotes"] = []

def save_state():
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state_data, f, ensure_ascii=False, indent=2)

GROUP_AI_SYSTEM_PROMPT = """
You are Zirak (زیرەک), a friendly, intelligent young Kurdish guy in a Telegram group chat.
You speak only in short, natural, human Sorani Kurdish (کوردیی سۆرانی ئاسایی چات).

Strict Rules:
1. NEVER translate machine English into Kurdish. Never use broken literal dictionary words.
2. Respond in 1 short, natural sentence as a real Kurdish friend in chat.
3. Use everyday Kurdish chat phrases (وەڵا, گیان, کاکە, ئاساییە, عافیەت بێت, هههه).
4. Be witty, friendly, and respectful.
"""

PRIVATE_AI_SYSTEM_PROMPT = """
You are Zirak (زیرەک), an exceptionally smart, polite, helpful, and knowledgeable AI assistant in private chat on Telegram.
You speak fluently in natural, beautiful, warm Sorani Kurdish (کوردیی سۆرانی ئاسایی و بەڕێز).

Strict Rules for Private Chat:
1. Answer any question (educational, general knowledge, technical, social, daily advice) intelligently, clearly, and helpfully.
2. Maintain a warm, friendly, respectful tone (گیان, بەڕێزم, کاکە, خوشکم).
3. Always respond in natural Sorani Kurdish without literal translation mistakes.
4. Keep answers concise, informative, and direct.
"""

WELCOME_MESSAGES = [
    "🌸 سڵاو {name} گیان! زۆر بەخێر هاتیت بۆ گروپەکەمان 🎉\n\nگەرمترین بەخێرهاتنت لێ دەکەین، هیواین کاتێکی زۆر خۆش و بەسوود لەگەڵمان بەسەر بپەڕێنیت! ✨❤️",
    "👑 سڵاو لە {name} خۆشەویست! زۆر بەخێربێیت بۆ نێو خێزانە چاک و ئازیزەکەمان 🌟\n\nخۆشحالین بە هاتنت، بە هیوای کاتی خۆش و سەرکەوتووانە! 🌺",
    "✨ سڵاو و دەرەکەت خۆش {name} گیان! بەخێربێیت بەسەر چاوانمان 💐\n\nگروپ بە هاتنی تۆ ڕووناک بووەوە! 🎉"
]

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
        "replies": ["من ناوم زیرەکە! هاوڕێیەکی دڵسۆزی کوردم 🤖❤️", "من زیرەکم! خزمەتکاری ئێوەی ئازیز 🌸"]
    }
]

# ───── 📚 وتەی جوانی کاتژمێری (Matching Clock Quotes & Wisdoms) ─────
FALLBACK_QUOTES = [
    "✨ *وتەی کاتژمێر:* مرۆڤ بە ڕەوشت و زانستەکەی گەورەیە، نەک بە سامانەکەی.",
    "🌸 *وتەی کاتژمێر:* هەرگیز ئومێد لەدەست مەدە، تاریكترین ساتەکانی شەو بەرهەمی سپێدەی ڕۆژێکی ڕووناکە.",
    "🌟 *وتەی کاتژمێر:* گەورەترین سەرمایەی مرۆڤ کاتە، بە شتی بەسوود بەسەری ببە.",
    "🌺 *وتەی کاتژمێر:* دڵخۆشی بەخشین بە دەوروبەرت، خۆشبەختیت بۆ دەگەڕێنێتەوە.",
    "🌿 *وتەی کاتژمێر:* وتەی جوان و زەردەخەنەیەک دەتوانێت دڵی هەزاران کەس بکاتەوە.",
    "💐 *وتەی کاتژمێر:* سەرکەوتن بەرهەمی کۆڵنەدان و هەوڵدانی بەردەوامە.",
    "☀️ *وتەی کاتژمێر:* بە باشی ڕوانین بۆ ئایندە، هەنگاوی یەکەمی سەرکەوتنە.",
    "🕊️ *وتەی کاتژمێر:* لە هەموو بارودۆخێکدا سوپاسگوزاری پەروەردگار بە.",
    "✨ *وتەی کاتژمێر:* ژیان وەک ئاوێنەیە، ئەگەر لێی خەندە بکەیت، ئەویش خەندەت بۆ دەکاتەوە.",
    "🌸 *وتەی کاتژمێر:* گەورەیی لەوەدا نییە کە هەرگیز نەکەویت، بەڵکو لەوەدایە دوای هەر کەوتنێک هەستیتەوە.",
    "🌟 *وتەی کاتژمێر:* باوەڕت بە خۆت هەبێت، چونکە تۆ دەتوانیت شتە مەزنەکان ئەنجام بدەیت.",
    "🌺 *وتەی کاتژمێر:* ئەو کەسەی دەیەوێت بگاتە لوتکە، نابێت لە ماندووبوون بترسێت.",
    "🌿 *وتەی کاتژمێر:* هەموو ڕۆژێک هەلێکی نوێیە بۆ باشتربوون.",
    "💐 *وتەی کاتژمێر:* زانست تاکە سامانێکە کە بە بەخشین زیاد دەکات.",
    "☀️ *وتەی کاتژمێر:* لێبوردەیی نیشانەی هێزە، نەک بێهێزی.",
    "🕊️ *وتەی کاتژمێر:* هەر شتێک لە دڵەوە بێت، دەگاتە دڵ.",
    "✨ *وتەی کاتژمێر:* سادەیی جوانترین جۆری پێشکەوتنە.",
    "🌸 *وتەی کاتژمێر:* ڕۆژانە هەوڵبدە ببیتە هۆکاری خەندەی کەسێک.",
    "🌟 *وتەی کاتژمێر:* بیرکردنەوەی ئەرێنی، کلیلی دەرگا داخراوەکانە.",
    "🌺 *وتەی کاتژمێر:* هەڵەکانمان وانەی ژیانن، نەک کۆتایی ڕێگاکە.",
    "🌿 *وتەی کاتژمێر:* چاکە بکە و لەبیری بکە، ڕۆژێک دێت بەری دەبینیت.",
    "💐 *وتەی کاتژمێر:* بەختەوەری لە ناخەوە هەڵدەقوڵێت، نەک لە دەوروبەرەوە.",
    "☀️ *وتەی کاتژمێر:* هیچ کاتێک درەنگ نییە بۆ خەونێکی نوێ.",
    "🕊️ *وتەی کاتژمێر:* ئارامگرتن تاڵە، بەڵام بەرهەمەکەی شیرینە.",
    "✨ *وتەی کاتژمێر:* ڕێزگرتن لە بەرامبەر، ڕێزگرتنە لە خودی خۆت.",
    "🌸 *وتەی کاتژمێر:* وشەی جوان وەک بارانی بەهارە، ڕۆح دەژێنێتەوە.",
    "🌟 *وتەی کاتژمێر:* هەنگاوی بچووک بەردەوام، باشترە لە هەنگاوی گەورەی پچڕ پچڕ.",
    "🌺 *وتەی کاتژمێر:* کاتە سەختەکان کەسە بەهێزەکان دروست دەکەن.",
    "🌿 *وتەی کاتژمێر:* ڕاستگۆیی گەورەترین سەرمایەی مرۆڤە.",
    "💐 *وتەی کاتژمێر:* ژیان کورتە، بە سادەیی و جوانی بژی.",
    "☀️ *وتەی کاتژمێر:* گەورەترین سەرکەوتن ئەوەیە کە زاڵ بیت بەسەر ناخی خۆتدا.",
    "🕊️ *وتەی کاتژمێر:* هیوا تاکە چرایەکە کە لە تاریکیدا ڕووناکی دەدات."
]

def generate_unique_quote():
    # Try groq API for unique quote
    try:
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))
        time_context = "شەو" if (now.hour >= 21 or now.hour < 5) else ("بەیانی" if now.hour < 12 else "پاشنیوەڕۆ")
        time_str = f"{now.hour}:{now.minute:02d}"
        
        if groq_client:
            res = groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": "You are a Kurdish AI. Provide EXACTLY ONE unique, beautiful, profound Sorani Kurdish quote, wisdom, or proverb. Never provide explanations, just the quote text. Make it poetic and meaningful. Do not repeat common quotes."},
                    {"role": "user", "content": f"Please give me a unique Sorani Kurdish quote suitable for this time of day ({time_context} at {time_str})."}
                ],
                max_tokens=150,
                temperature=0.9
            )
            ans = res.choices[0].message.content.strip()
            ans = ans.replace('"', '').replace("'", "")
            if ans:
                return f"✨ *وتەی کاتژمێر:*\n\n{ans}"
    except Exception as e:
        print("Groq Quote Error:", e)
        
    # Fallback Mechanism
    available_quotes = [q for q in FALLBACK_QUOTES if q not in state_data["sent_quotes"]]
    if not available_quotes:
        state_data["sent_quotes"] = []
        available_quotes = FALLBACK_QUOTES
        
    chosen = random.choice(available_quotes)
    state_data["sent_quotes"].append(chosen)
    save_state()
    return chosen

# ───── 🕌 زیکر و بیریاری کاتی نوێژەکان (Prayer Messages) ─────
PRAYER_MESSAGES = {
    "Fajr": "🕌 **کاتی نوێژی بەیانییە (فەجر)** 🌸\n\n﴿إِنَّ قُرْآنَ الْفَجْرِ كَانَ مَشْهُودًا﴾\nسەڵاوات لەسەر پێغەمبەری خوا (ﷺ) لێبدەن: أللَّهُمَّ صَلِّ عَلَى مُحَمَّدٍ وَعَلَى آلِ مُحَمَّدٍ 🤍",
    "Dhuhr": "🕌 **کاتی نوێژی نیوەڕۆیە (ژوهر)** 🌸\n\nزیکری پیرۆز: سُبْحَانَ اللَّهِ وَبِحَمْدِهِ ، سُبْحَانَ اللَّهِ الْعَظِيمِ ✨",
    "Asr": "🕌 **کاتی نوێژی عەسردایە** 🌸\n\nزیکری پیرۆز: لا إِلَهَ إِلا اللَّهُ وَحْدَهُ لا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ 🌿",
    "Maghrib": "🕌 **کاتی نوێژی ئێوارەیە (مەغریب)** 🌸\n\nزیکری پیرۆز: أَسْتَغْفِرُ اللَّهَ وَأَتُوبُ إِلَيْهِ 💐",
    "Isha": "🕌 **کاتی نوێژی عیشایە (خەوتنان)** 🌸\n\nزیکری پیرۆز: لا حَوْلَ وَلا قُوَّةَ إِلا بِاللَّهِ الْعَلِيِّ الْعَظِيمِ 🌟"
}

# کاتی نوێژەکان بۆ کوردستان (Erbil / Kurdistan UTC+3)
LIVE_PRAYER_TIMES = {
    "Fajr": "03:37",
    "Dhuhr": "12:10",
    "Asr": "15:57",
    "Maghrib": "19:05",
    "Isha": "20:36"
}

# ───── 🛡️ فیلتەری زۆر توندی جنێو و وشەی ناشرین (Precise Word Boundaries) ─────
STANDALONE_BAD_WORDS = ['قن', 'گو', 'کیر', 'کێر', 'تڕ']

EXPLICIT_BAD_WORDS = [
    'قنت', 'قنم', 'قنی', 'قوز', 'قۆز', 'قوزت', 'قوزم', 'قوزی',
    'کێرم', 'کیرم', 'کێری', 'کێرت', 'کیرت',
    'گواو', 'گوخۆر', 'گوو', 'گو', 'گوت', 'گووم', 'گواوی',
    'حیز', 'سۆزانی', 'سێکس', 'پۆرن', 'قەحبە', 'گەواد', 'پینتی', 'بێنامووس',
    'ئەتگێم', 'ئەگێم', 'بگێم', 'بگێرم', 'تێبگێم', 'گاین', 'تێگەین', 'بگێین', 'داپێنم',
    'fuck', 'f\\s*u\\s*c\\s*k', 'shit', 'bitch', 'asshole', 'dick', 'pussy',
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

def is_forwarded_message(msg: dict) -> bool:
    return any(k in msg for k in ["forward_date", "forward_from", "forward_from_chat", "forward_sender_name"])

# ═══════════════════════════════════════════════════════════════════════════════
#  تەواوی فەنکشنەکانی تیلیگرام
# ═══════════════════════════════════════════════════════════════════════════════

def tg_call(method: str, payload: dict = None):
    try:
        r = requests.post(f"{API_BASE}/{method}", json=payload or {}, timeout=30)
        return r.json()
    except Exception as e:
        print(f"Telegram API Error ({method}):", e)
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
        status = res["result"]["status"]
        return status in ["creator", "administrator"]
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

def clean_ai_text(text: str) -> str:
    if not text:
        return ""
    clean = re.sub(r'(?im)^\s*@?[a-zA-Z0-9_]+:\s*', '', text)
    clean = re.sub(r'\([^()\r\n]*\)', '', clean)
    if re.search(r'[\u0900-\u097F]', clean):
        return ""
    return clean.strip()

def get_smart_reply(text: str):
    lower = text.strip().lower()
    for entry in SMART_REPLIES:
        for p in entry["patterns"]:
            if p in lower:
                return random.choice(entry["replies"])
    return None

def get_ai_reply(chat_id: int, user_id: int, question: str, is_private: bool = False) -> str:
    smart = get_smart_reply(question)
    if smart:
        return smart

    if not groq_client:
        return "گیان لە خزمەتتم، چی پرسیارێکت هەبێت فەرموو؟ 😊"

    system_prompt = PRIVATE_AI_SYSTEM_PROMPT if is_private else GROUP_AI_SYSTEM_PROMPT
    max_tokens = 250 if is_private else 120

    try:
        res = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            max_tokens=max_tokens,
            temperature=0.5
        )
        answer = res.choices[0].message.content
        answer = clean_ai_text(answer)
        if answer:
            return answer
    except Exception as e:
        print("Groq Error:", e)

    return "گیان لە خزمەتتم، دەتوانیت دووبارە ڕوونی بکەیتەوە؟ 🌸"

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
    'سێکس', 'سێکسی', 'پۆرن', 'ڕووت', 'قوز', 'قۆز', 'کێر', 'کیر', 'حیز', 'سۆزانی',
    'قەحبە', 'گەواد', 'گاین', 'داپێنم', 'پینتی', 'گوان', 'مەمک', 'قن', 'کۆم', '18+', '+18'
]

def check_image_nsfw_ai(file_id: str) -> bool:
    """پشکنینی بینراوی وێنە و ستیکەر بە ژیریی دەستکردی Vision بۆ دۆزینەوەی ناوەڕۆکی سێکسی"""
    if not file_id:
        return False
    try:
        file_info = tg_call("getFile", {"file_id": file_id})
        if not file_info or not file_info.get("ok"):
            return False
        file_path = file_info["result"].get("file_path", "")
        if not file_path:
            return False

        if file_path.endswith(".tgs"):
            return False
            
        img_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        proxies = {
            "http": "http://proxy.server:3128",
            "https": "http://proxy.server:3128"
        } if (os.path.exists("/home/ramanyousif2002") or "PYTHONANYWHERE_DOMAIN" in os.environ) else None
        
        img_res = requests.get(img_url, proxies=proxies, timeout=8)
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

        v_url = "https://api.groq.com/openai/v1/chat/completions"
        v_headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        v_payload = {
            "model": "llama-3.2-11b-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Is this image pornographic, sexually explicit, depicting nudity, sexual intercourse, genitals, or adult +18 NSFW content? Reply with ONLY 'YES' or 'NO'."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64_img}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 10,
            "temperature": 0.1
        }
        r = requests.post(v_url, headers=v_headers, json=v_payload, proxies=proxies, timeout=10)
        res_data = r.json()
        if "choices" in res_data and len(res_data["choices"]) > 0:
            ans = res_data["choices"][0]["message"]["content"].strip().upper()
            if "YES" in ans:
                return True
    except Exception as e:
        print(f"Vision AI check exception: {e}")
    return False

def is_nsfw_media(msg: dict) -> bool:
    """پشکنینی وردی ستیکەر، گیف، ڤیدیۆ و وێنە بۆ شتی نەشیاو و +18"""
    thumb_id = None

    if "sticker" in msg:
        st = msg["sticker"]
        set_name = (st.get("set_name") or "").lower()
        emoji = st.get("emoji") or ""
        
        if "🔞" in emoji:
            return True
            
        if set_name:
            norm_set = normalize_kurdish(set_name.replace('_', ' ').replace('-', ' ').replace('.', ' '))
            for kw in NSFW_KEYWORDS:
                if kw in set_name or kw in norm_set:
                    return True
            if contains_bad_word(norm_set):
                return True

        if st.get("thumbnail"):
            thumb_id = st["thumbnail"].get("file_id")
        elif not st.get("is_video") and not st.get("is_animated"):
            thumb_id = st.get("file_id")
        elif st.get("is_video"):
            thumb_id = st.get("thumbnail", {}).get("file_id") or st.get("file_id")

    doc = msg.get("animation") or msg.get("document") or msg.get("video") or {}
    if doc:
        f_name = (doc.get("file_name") or "").lower()
        if f_name:
            norm_fn = normalize_kurdish(f_name.replace('_', ' ').replace('-', ' ').replace('.', ' '))
            for kw in NSFW_KEYWORDS:
                if kw in f_name or kw in norm_fn:
                    return True
            if contains_bad_word(norm_fn):
                return True
        if not thumb_id:
            thumb_id = doc.get("thumbnail", {}).get("file_id") or doc.get("file_id")

    cap = (msg.get("caption") or "").lower()
    if cap:
        norm_cap = normalize_kurdish(cap)
        for kw in NSFW_KEYWORDS:
            if kw in cap or kw in norm_cap:
                return True

    if "photo" in msg and msg["photo"]:
        if not thumb_id:
            thumb_id = msg["photo"][-1].get("file_id")

    if thumb_id:
        if check_image_nsfw_ai(thumb_id):
            return True

    return False

# ═══════════════════════════════════════════════════════════════════════════════
#  سیستەمی قوفڵی ئەتۆمی بۆ ڕێگریکردن لە دووبارەبوونەوە (Atomic Schedule Lock)
# ═══════════════════════════════════════════════════════════════════════════════

LOCK_DIR = Path("/home/ramanyousif2002/zirak-bot/data/locks") if (os.path.exists("/home/ramanyousif2002") or "PYTHONANYWHERE_DOMAIN" in os.environ) else Path("data/locks")

def claim_schedule_lock(lock_name: str, stamp: str) -> bool:
    try:
        LOCK_DIR.mkdir(parents=True, exist_ok=True)
        safe_stamp = re.sub(r'[^a-zA-Z0-9_\-]', '_', stamp)
        lock_file = LOCK_DIR / f"{lock_name}_{safe_stamp}.lock"
        
        fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, 'w') as f:
            f.write(str(time.time()))
        
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
#  تایبەتمەندیی نوێ: کاتژمێرە هاوشێوەکان (1:01, 2:02 ...) و کاتی نوێژەکان
# ═══════════════════════════════════════════════════════════════════════════════

LAST_HOURLY_CHECK = ""
LAST_PRAYER_CHECK = ""
LAST_API_FETCH_DAY = ""

def fetch_live_prayer_times():
    global LIVE_PRAYER_TIMES, LAST_API_FETCH_DAY
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    if LAST_API_FETCH_DAY == today_str:
        return
    try:
        r = requests.get("http://api.aladhan.com/v1/timingsByCity?city=Erbil&country=Iraq&method=3", timeout=10)
        data = r.json()
        if data and data.get("code") == 200:
            timings = data["data"]["timings"]
            LIVE_PRAYER_TIMES["Fajr"] = timings.get("Fajr", "03:37")
            LIVE_PRAYER_TIMES["Dhuhr"] = timings.get("Dhuhr", "12:10")
            LIVE_PRAYER_TIMES["Asr"] = timings.get("Asr", "15:57")
            LIVE_PRAYER_TIMES["Maghrib"] = timings.get("Maghrib", "19:05")
            LIVE_PRAYER_TIMES["Isha"] = timings.get("Isha", "20:36")
            LAST_API_FETCH_DAY = today_str
    except Exception as e:
        print("Aladhan API fetch exception:", e)

def broadcast_to_groups(text: str):
    if not text:
        return
    groups = state_data.get("groups", {})
    for g_id_str in list(groups.keys()):
        try:
            send_message(int(g_id_str), text)
        except Exception as e:
            print(f"Broadcast error for {g_id_str}:", e)

def check_scheduled_tasks():
    # Kurdistan Timezone (UTC+3)
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))
    current_time_str = now.strftime("%H:%M")
    current_stamp_str = now.strftime("%Y-%m-%d %H:%M")

    # 1:01, 2:02, 3:03, 4:04, 5:05, 6:06, 7:07, 8:08, 9:09, 10:10, 11:11, 12:12
    h12 = now.hour % 12
    if h12 == 0:
        h12 = 12

    is_matching_time = (now.minute == h12)

    # ١. پشکنینی کاتژمێرە هاوشێوەکان (1:01, 2:02 ... 11:11, 12:12) + یەک وتەی جوان
    if is_matching_time:
        if claim_schedule_lock("clock", current_stamp_str):
            period = "شەو" if (now.hour >= 21 or now.hour < 5) else ("بەیانی" if now.hour < 12 else "پاشنیوەڕۆ")
            digits_kurdish = {"0":"۰", "1":"۱", "2":"۲", "3":"۳", "4":"٤", "5":"٥", "6":"٦", "7":"٧", "8":"٨", "9":"٩"}
            k_hour = "".join([digits_kurdish.get(c, c) for c in str(h12)])
            k_min = "".join([digits_kurdish.get(c, c) for c in f"{now.minute:02d}"])
            
            quote = generate_unique_quote()
            clock_msg = f"🕐 *کاتژمێر {k_hour}:{k_min} ی {period}ە* ✨\n\n{quote}"
            broadcast_to_groups(clock_msg)

    # ٢. پشکنینی کاتی نوێژەکان (بانگ و زیکر)
    fetch_live_prayer_times()
    for prayer_name, prayer_time in LIVE_PRAYER_TIMES.items():
        if current_time_str == prayer_time:
            p_check_key = f"{now.strftime('%Y-%m-%d')}_{prayer_name}"
            if claim_schedule_lock("prayer", p_check_key):
                prayer_msg = PRAYER_MESSAGES.get(prayer_name, "")
                if prayer_msg:
                    broadcast_to_groups(prayer_msg)

# ═══════════════════════════════════════════════════════════════════════════════
#  بەڕێوەبردنی پەیامەکان (Message Processor)
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

    # تۆمارکردنی ئایدی گروپەکە تاوەکو کاتی کاتژمێر و نوێژەکانی بۆ ڕەوانە بکرێت
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

    # 💬 ۱. چاتی شەخسی (Private Chat)
    if chat_type == "private":
        if text:
            reply = get_ai_reply(chat_id, user_id, text, is_private=True)
            if reply:
                send_message(chat_id, reply, msg_id)
        return

    # 🛡️ ۲. ئاسایشی توندی گروپ (ستیکەری نەشیاو، قسەی ناشرین و لینک)
    is_user_admin = is_admin(chat_id, user_id)
    msg_is_fwd = is_forwarded_message(msg)

    # ئەگەر ستیکەر، گیف یان وێنەی سێکسی و +18 بێت ڕاستەوخۆ دەسڕدرێتەوە
    if is_nsfw_media(msg):
        delete_message(chat_id, msg_id)
        if not is_user_admin:
            cnt = add_user_warning(chat_id, user_id)
            send_message(chat_id, f"⚠️ {display_name} ناردنی ستیکەر یان وێنەی نەشیاو و +18 🔞 قەدەغەیە! ئاگاداری: ({cnt}/{MAX_WARNINGS})")
            if cnt >= MAX_WARNINGS:
                set_user_mute(chat_id, user_id, AUTO_MUTE_MINUTES)
                send_message(chat_id, f"🚫 {display_name} بەهۆی ناردنی شتی نەشیاو، بۆ ماوەی ١ کاتژمێر لە چاتکردن بێدەنگ کرا!")
        return

    if not is_user_admin:
        violation = ""

        if contains_link_or_spam(msg, text):
            violation = "ناردنی لینک، پۆست یان ریپڵای دوگمەدار 🔗"
        elif contains_bad_word(text):
            violation = "قسەی ناشرین و جنێو 🤬"

        if violation:
            delete_message(chat_id, msg_id)
            cnt = add_user_warning(chat_id, user_id)
            send_message(chat_id, f"⚠️ {display_name} {violation} قەدەغەیە! ئاگاداری: ({cnt}/{MAX_WARNINGS})")
            if cnt >= MAX_WARNINGS:
                set_user_mute(chat_id, user_id, AUTO_MUTE_MINUTES)
                send_message(chat_id, f"🚫 {display_name} بەهۆی دووبارەکردنەوەی سەرپێچی، بۆ ماوەی ١ کاتژمێر لە چاتکردن بێدەنگ کرا!")
            return

    # 💬 ۳. وەڵامدانەوەی AI لە گروپدا
    if text:
        should_ai_reply = True
        if "reply_to_message" in msg and msg["reply_to_message"]:
            target_user = msg["reply_to_message"].get("from", {})
            target_id = target_user.get("id", 0)
            is_target_bot = target_user.get("is_bot", False)
            if target_id != BOT_ID and not is_target_bot:
                should_ai_reply = False

        if should_ai_reply:
            reply = get_ai_reply(chat_id, user_id, text, is_private=False)
            if reply:
                send_message(chat_id, reply, msg_id)

def main():
    tg_call("deleteWebhook", {"drop_pending_updates": True})
    print("===============================================")
    print("  Zirak Security & AI Bot (Python Cloud Engine)")
    print("===============================================")

    offset = 0
    while True:
        try:
            # 🕒 پشکنینی ئۆتۆماتیکیی کاتی نوێژەکان و کاتژمێرە هاوشێوەکان
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
    main()
