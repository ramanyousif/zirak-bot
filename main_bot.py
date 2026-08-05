# -*- coding: utf-8 -*-
"""
بوتی زیرەک - Zirak Telegram Security & AI Bot (24/7 Cloud Ready)
"""

import os
import re
import json
import time
import random
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
        state_data = {"warnings": {}, "ai_history": {}}
else:
    state_data = {"warnings": {}, "ai_history": {}}

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

# ───── 🛡️ فیلتەری زۆر توندی جنێو و وشەی ناشرین ─────
BAD_WORDS_LIST = [
    'قن', 'قنت', 'قنم', 'قنی', 'قوز', 'قۆز', 'قوزت', 'قوزم', 'قوزی',
    'کیر', 'کێرم', 'کیرم', 'کێر', 'کێری', 'کێرت', 'کیرت',
    'گواو', 'گوخۆر', 'گوو', 'گو', 'گوت', 'گووم', 'گواوی',
    'حیز', 'سۆزانی', 'سێکس', 'پۆرن', 'قەحبە', 'گەواد', 'پینتی', 'بێنامووس', 'نامووس',
    'ئەتگێم', 'ئەگێم', 'بگێم', 'بگێرم', 'تێبگێم', 'گاین', 'تێگەین', 'بگێین', 'داپێنم',
    'fuck', 'f\\s*u\\s*c\\s*k', 'shit', 'bitch', 'asshole', 'dick', 'pussy',
    'bastard', 'whore', 'slut', 'nigger', 'faggot', 'cock', 'cunt',
    'motherf', 'stfu', 'porn', 'xxx', 'nude', 'naked',
    'boobs', 'tits', 'penis', 'vagina', 'orgasm', 'hentai'
]

BAD_PHRASES_LIST = [
    r'لە\s*دایکت', r'دایکت\s*بگێم', r'دایکت\s*گێم', r'دایکت\s*بێ', r'دایکت\s*بم', r'دایکت\s*بکێم',
    r'لە\s*خوشکت', r'خوشکت\s*بگێم', r'خوشکت\s*گێم', r'خوشکت\s*بێ', r'خوشکت\s*بم', r'خوشکت\s*بکێم',
    r'لە\s*عەرزت', r'لە\s*قەبرت', r'داپیرەت\s*بم', r'بێ\s*دایک', r'بێ\s*خوشک', r'سەر\s*قن', r'کێرم\s*لە'
]

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
    body = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
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
        return "گیان لە خزمەتتم، چی پرسیارێکت هەیە فەرموو؟ 😊"

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
    lower = text.lower()
    
    # 1. Check direct profanity substring
    for w in BAD_WORDS_LIST:
        if w in lower:
            return True
            
    # 2. Check profanity phrases via regex
    for phrase in BAD_PHRASES_LIST:
        if re.search(phrase, lower, re.IGNORECASE):
            return True
            
    return False

def contains_link_or_spam(msg: dict, text: str) -> bool:
    if text and re.search(r'(?i)\bhttps?://|\bt\.me/|\btelegram\.me/|\bwww\.|@[a-zA-Z0-9_]{4,}', text):
        return True
    if msg.get("entities"):
        for e in msg["entities"]:
            if e.get("type") in ["url", "text_link", "mention"]:
                return True
    if msg.get("caption_entities"):
        for e in msg["caption_entities"]:
            if e.get("type") in ["url", "text_link", "mention"]:
                return True
    if msg.get("reply_markup"):
        return True
    if any(k in msg for k in ["forward_date", "forward_from", "forward_from_chat", "forward_sender_name"]):
        return True
    return False

def handle_message(msg: dict):
    if "chat" not in msg or "from" not in msg:
        return
    chat = msg["chat"]
    chat_type = chat["type"]
    if chat_type not in ["group", "supergroup", "private"]:
        return

    chat_id = chat["id"]
    msg_id = msg["message_id"]
    from_user = msg["from"]
    user_id = from_user["id"]
    display_name = get_display_name(from_user)

    # 🌸 بەخێرهاتنی ئەندامانی نوێ
    if "new_chat_members" in msg:
        for member in msg["new_chat_members"]:
            if member.get("is_bot"):
                continue
            m_name = get_display_name(member)
            w_msg = random.choice(WELCOME_MESSAGES).format(name=m_name)
            send_message(chat_id, w_msg, msg_id)

    text = msg.get("text") or msg.get("caption") or ""

    # 💬 ۱. چاتی شەخسی (Private Chat) - وەڵامدانەوەی زیرەکانەی هەموو پرسیارێک بە کوردی
    if chat_type == "private":
        if text:
            reply = get_ai_reply(chat_id, user_id, text, is_private=True)
            if reply:
                send_message(chat_id, reply, msg_id)
        return

    # 🛡️ ۲. ئاسایشی توندی گروپ (بۆ نا-ئەدمین)
    is_user_admin = is_admin(chat_id, user_id)
    if not is_user_admin:
        violation = ""
        if "photo" in msg:
            violation = "ناردنی وێنە 📷"
        elif "video" in msg or "video_note" in msg:
            violation = "ناردنی ڤیدیۆ 🎥"
        elif "animation" in msg or "document" in msg:
            violation = "ناردنی GIF / فۆرمات / فایل 🎬"
        elif "sticker" in msg:
            violation = "ناردنی ستیکەر 🎭"
        elif "voice" in msg or "audio" in msg:
            violation = "ناردنی فایلی دەنگی 🎙️"
        elif contains_link_or_spam(msg, text):
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

    # 💬 ۳. وەڵامدانەوەی AI لە گروپدا (بەمەرجی بێدەنگبوون کاتێک مرۆڤ ریپڵای مرۆڤ دەکات)
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
            res = tg_call("getUpdates", {"offset": offset, "timeout": 30})
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
