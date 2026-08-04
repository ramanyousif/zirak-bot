# Telegram Group Protection Bot

Bot username: `mygrouppatwmat_bot`

ئەم botە بە PowerShell کار دەکات و پێویستی بە Python/Node نییە.

## 1. Token دابنێ

لە BotFather ئەو tokenە وەربگرە کە بۆ botەکەت دراوە. پاشان یەکێک لەم دوو ڕێگایە بکە:

### ڕێگای باشتر: environment variable

```powershell
$env:TELEGRAM_BOT_TOKEN="123456:ABC..."
.\bot.ps1
```

### یان config file

`config.example.json` بکە بە `config.json` و tokenەکەی تێدا بنووسە.

## 2. Bot زیاد بکە بۆ گروپ

1. `mygrouppatwmat_bot` زیاد بکە بۆ گروپەکەت.
2. بیکە `Admin`.
3. ئەم مۆڵەتانەی پێبدە:
   - Delete messages
   - Ban users
   - Restrict members
4. لە BotFather بۆ botەکەت `Group Privacy` بکە `Off`، چونکە botی پاراستن پێویستی بە بینینی نامەکانی گروپ هەیە.

## 3. هەڵکردن

```powershell
.\bot.ps1
```

## فەرمانەکان

تەنها admin دەتوانێت فەرمانی سزا بەکاربهێنێت.

- `/help` - پیشاندانی فەرمانەکان
- `/id` - پیشاندانی chat id
- `/rules` - پیشاندانی یاساکان
- `/setrules متن` - دانانی یاساکانی گروپ
- `/warn` - وەڵام بدەوە بە نامەی کەسێک و ئاگاداری بدە
- `/warnings` - وەڵام بدەوە و ژمارەی ئاگاداری ببینە
- `/mute 10m` - وەڵام بدەوە و بۆ ماوەیەک بێدەنگی بکە
- `/ban` - وەڵام بدەوە و بەکارهێنەر ban بکە
- `/unban user_id` - ban لاببە

## پاراستنە چالاکەکان

- سڕینەوەی لینک لە ئەندامی نائەدمین
- دۆزینەوەی flood/spam
- ئاگاداری خودکار
- muteی خودکار دوای ئاگاداری زۆر
- بەخێرهاتنی ئەندامی نوێ

داتا لە `data/state.json` پاشەکەوت دەکرێت.
