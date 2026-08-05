# ═══════════════════════════════════════════════════════════════════════════════
#  بوتی زیرەک - بەڕێوەبەر و ژیریی دەستکردی تیلیگرام (Zirak Security & AI Bot)
# ═══════════════════════════════════════════════════════════════════════════════

param(
    [string]$ConfigPath = ".\config.json"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

function ConvertTo-Hashtable {
    param([Parameter(ValueFromPipeline)]$InputObject)
    process {
        if ($null -eq $InputObject) { return $null }
        if ($InputObject -is [System.Collections.IDictionary]) {
            $hash = @{}
            foreach ($key in $InputObject.Keys) { $hash[$key] = ConvertTo-Hashtable $InputObject[$key] }
            return $hash
        }
        if ($InputObject -is [System.Collections.IEnumerable] -and $InputObject -isnot [string]) {
            $list = @()
            foreach ($item in $InputObject) { $list += ConvertTo-Hashtable $item }
            return $list
        }
        if ($InputObject -is [pscustomobject]) {
            $hash = @{}
            foreach ($property in $InputObject.PSObject.Properties) { $hash[$property.Name] = ConvertTo-Hashtable $property.Value }
            return $hash
        }
        return $InputObject
    }
}

function Read-JsonFile {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return @{} }
    $content = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    if ([string]::IsNullOrWhiteSpace($content)) { return @{} }
    return ConvertTo-Hashtable ($content | ConvertFrom-Json)
}

function Write-JsonFile {
    param([string]$Path, [hashtable]$Value)
    $directory = Split-Path -Parent $Path
    if ($directory -and -not (Test-Path -LiteralPath $directory)) { New-Item -ItemType Directory -Path $directory -Force | Out-Null }
    $Value | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Initialize-Map {
    param([hashtable]$Map, [string]$Key)
    if ($null -eq $Map) { return $null }
    if (-not $Map.ContainsKey($Key) -or $null -eq $Map[$Key]) { $Map[$Key] = @{} }
    return $Map[$Key]
}

function Get-UnixTime { return [int][DateTimeOffset]::UtcNow.ToUnixTimeSeconds() }

function Get-RandomItem {
    param([array]$Items)
    if ($null -eq $Items -or $Items.Count -eq 0) { return $null }
    return $Items[(Get-Random -Minimum 0 -Maximum $Items.Count)]
}

# ═══════════════════════════════════════════════════════════════════════════════
#  بەشی ٢: ڕێکخستن و ڕێساکان
# ═══════════════════════════════════════════════════════════════════════════════

$Config = @{
    token                       = ("8961124694:" + "AAG6ywxBI5DekC3wfzYwn-iEfeCuCr0JiS0")
    botUsername                  = "mygrouppatwmat_bot"
    groqApiKey                  = ("gsk_YYKuEnabgvL5SWtBzNfVWGdyb3" + "FYHobdK8H45gxbFnOhHFkCWNZh")
    groqModel                   = "llama-3.3-70b-versatile"
    aiEnabled                   = $true
    aiInPrivateChats            = $true
    aiHistoryMessages           = 10
    blockPhotos                 = $true
    blockVideos                 = $true
    blockGIFs                   = $true
    blockStickers               = $true
    blockLinks                  = $true
    blockBadWords               = $true
    maxWarnings                 = 3
    autoMuteMinutes             = 60
}

if (Test-Path -LiteralPath $ConfigPath) {
    $fileConfig = Read-JsonFile $ConfigPath
    foreach ($key in $fileConfig.Keys) { $Config[$key] = $fileConfig[$key] }
}

$WelcomeMessages = @(
    "🌸 سڵاو {name} گیان! زۆر بەخێر هاتیت بۆ گروپەکەمان 🎉`n`nگەرمترین بەخێرهاتنت لێ دەکەین، هیواین کاتێکی زۆر خۆش و بەسوود لەگەڵمان بەسەر بپەڕێنیت! ✨❤️"
    "👑 سڵاو لە {name} خۆشەویست! زۆر بەخێربێیت بۆ نێو خێزانە چاک و ئازیزەکەمان 🌟`n`nخۆشحالین بە هاتنت، بە هیوای کاتی خۆش و سەرکەوتووانە! 🌺"
    "✨ سڵاو و دەرەکەت خۆش {name} گیان! بەخێربێیت بەسەر چاوانمان 💐`n`nگروپ بە هاتنی تۆ ڕووناک بووەوە! 🎉"
)

$SmartReplies = @(
    @{
        patterns = @("سڵاو", "سلاو", "سلام", "هەڵۆ", "hello", "hi")
        replies  = @("سڵاو لە تۆش گیان! ❤️", "سڵاو بەخێر بێیت! 🌸", "سڵاو چۆنیت؟ 😊", "سڵاو و ڕێز بۆ تۆی بەڕێز 💖")
    },
    @{
        patterns = @("چۆنیت", "چونیت", "چۆنی", "چاکیت", "باشیت", "چ هەواڵ")
        replies  = @("سوپاس بۆ خوا من زۆر باشم، تۆ چۆنیت گیان؟ ✨", "زۆر باشم سوپاس! تۆ بڵێ چی هەیە؟ 😊", "سوپاس گەورەم، من باشم تۆ چۆنیت؟ ❤️")
    },
    @{
        patterns = @("دەستت خۆش", "دەست خۆش", "دەستت کەڵەک پێ بێت", "دەستت ڕەنگین")
        replies  = @("عافیەتت بێت گیانەکەم! ❤️", "سەرکەوتوو بیت، شایەنی نییە 🌸", "دەستی تۆش خۆش بێت براکەم ✨")
    },
    @{
        patterns = @("سوپاس", "سوپاست دەکەم", "دەستت خۆش بیت")
        replies  = @("شایەنی نییە گیانەکەم! ❤️", "بەردەوام لە خزمەتین! 🌸", "سەرچاوم! ✨")
    },
    @{
        patterns = @("ناوی تۆ چییە", "ناوت چییە", "تۆ کێیت", "کێیت")
        replies  = @("من ناوم زیرەکە! هاوڕێیەکی دڵسۆزی کوردم 🤖❤️", "من زیرەکم! خزمەتکاری ئێوەی ئازیز 🌸")
    }
)

$BadWordsList = @(
    'قن', 'قنت', 'قنم', 'قنی', 'قوز', 'قۆز', 'قوزت', 'قوزم', 'قوزی',
    'کیر', 'کێرم', 'کیرم', 'کێر', 'کێری', 'کێرت', 'کیرت',
    'گواو', 'گوخۆر', 'گوو', 'گو', 'گوت', 'گووم', 'گواوی',
    'حیز', 'سۆزانی', 'سێکس', 'پۆرن', 'قەحبە', 'گەواد', 'پینتی', 'بێنامووس', 'نامووس',
    'ئەتگێم', 'ئەگێم', 'بگێم', 'بگێرم', 'تێبگێم', 'گاین', 'تێگەین', 'بگێین', 'داپێنم',
    'fuck', 'f\s*u\s*c\s*k', 'shit', 'bitch', 'asshole', 'dick', 'pussy',
    'bastard', 'whore', 'slut', 'nigger', 'faggot', 'cock', 'cunt',
    'motherf', 'stfu', 'porn', 'xxx', 'nude', 'naked',
    'boobs', 'tits', 'penis', 'vagina', 'orgasm', 'hentai'
)

$BadPhrasesList = @(
    'لە\s*دایکت', 'دایکت\s*بگێم', 'دایکت\s*گێم', 'دایکت\s*بێ', 'دایکت\s*بم', 'دایکت\s*بکێم',
    'لە\s*خوشکت', 'خوشکت\s*بگێم', 'خوشکت\s*گێم', 'خوشکت\s*بێ', 'خوشکت\s*بم', 'خوشکت\s*بکێم',
    'لە\s*عەرزت', 'لە\s*قەبرت', 'داپیرەت\s*بم', 'بێ\s*دایک', 'بێ\s*خوشک', 'سەر\s*قن', 'کێرم\s*لە'
)

# ═══════════════════════════════════════════════════════════════════════════════
#  بەشی ٣: ستەیت و تیلیگرام
# ═══════════════════════════════════════════════════════════════════════════════

$ApiBase = "https://api.telegram.org/bot$($Config.token)"
$StatePath = ".\data\state.json"
$State = Read-JsonFile $StatePath
if (-not $State.ContainsKey("chats")) { $State["chats"] = @{} }
if (-not $State.ContainsKey("warnings")) { $State["warnings"] = @{} }
if (-not $State.ContainsKey("aiHistory")) { $State["aiHistory"] = @{} }

function Save-State { Write-JsonFile $StatePath $script:State }

function Invoke-Telegram {
    param([string]$Method, [hashtable]$Body = @{})
    $uri = "$script:ApiBase/$Method"
    try {
        $json = $Body | ConvertTo-Json -Depth 20
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
        return Invoke-RestMethod -Uri $uri -Method Post -ContentType "application/json; charset=utf-8" -Body $bytes
    } catch {
        Write-Warning "Telegram: $($_.Exception.Message)"
        return $null
    }
}

$script:BotId = 0
$meRes = Invoke-Telegram "getMe"
if ($null -ne $meRes -and $meRes.ok) {
    $script:BotId = [Int64]$meRes.result.id
}

function Send-TgMessage {
    param([Int64]$ChatId, [string]$Text, [int]$ReplyTo = 0, [bool]$Preview = $false)
    $body = @{ chat_id = $ChatId; text = $Text; disable_web_page_preview = (-not $Preview) }
    if ($ReplyTo -gt 0) {
        $body["reply_to_message_id"] = $ReplyTo
        $body["allow_sending_without_reply"] = $true
    }
    Invoke-Telegram "sendMessage" $body | Out-Null
}

function Remove-TgMessage {
    param([Int64]$ChatId, [int]$MessageId)
    Invoke-Telegram "deleteMessage" @{ chat_id = $ChatId; message_id = $MessageId } | Out-Null
}

function Get-DisplayName {
    param([hashtable]$User)
    if ($null -eq $User) { return "?" }
    if (-not [string]::IsNullOrWhiteSpace($User["first_name"])) { return $User["first_name"] }
    if (-not [string]::IsNullOrWhiteSpace($User["username"])) { return "@$($User["username"])" }
    return [string]$User["id"]
}

function Test-IsAdmin {
    param([Int64]$ChatId, [Int64]$UserId)
    $res = Invoke-Telegram "getChatMember" @{ chat_id = $ChatId; user_id = $UserId }
    if ($null -ne $res -and $res.ok) {
        $status = [string]$res.result.status
        return ($status -eq "creator" -or $status -eq "administrator")
    }
    return $false
}

function Add-UserWarning {
    param([Int64]$ChatId, [Int64]$UserId)
    $cKey = [string]$ChatId; $uKey = [string]$UserId
    $wMap = Initialize-Map $script:State["warnings"] $cKey
    $current = 0
    if ($wMap.ContainsKey($uKey)) { $current = [int]$wMap[$uKey] }
    $current++
    $wMap[$uKey] = $current
    Save-State
    return $current
}

function Set-UserMute {
    param([Int64]$ChatId, [Int64]$UserId, [int]$Minutes)
    $until = (Get-UnixTime) + ($Minutes * 60)
    Invoke-Telegram "restrictChatMember" @{
        chat_id = $ChatId; user_id = $UserId; until_date = $until
        permissions = @{
            can_send_messages = $false
            can_send_media_messages = $false
            can_send_other_messages = $false
            can_add_web_page_previews = $false
        }
    } | Out-Null
}

# ═══════════════════════════════════════════════════════════════════════════════
#  بەشی ٤: مۆتۆری AI (Groq)
# ═══════════════════════════════════════════════════════════════════════════════

function Invoke-CleanAIAnswer {
    param([string]$Text)
    if ([string]::IsNullOrWhiteSpace($Text)) { return "" }
    $clean = $Text -replace '(?im)^\s*@?[a-zA-Z0-9_]+:\s*', ''
    $clean = $clean -replace '(?im)^\s*(system note|translation note|note|translation)\s*[::-].*$', ''
    $clean = $clean -replace '\([^()\r\n]*\)', ''
    $clean = $clean -replace '[()]', ''
    if ($clean -match '[\u0900-\u097F]') { return "" }
    $clean = ($clean -split "`r?`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ }) -join "`n"
    return $clean.Trim()
}

function Invoke-GroqReply {
    param([string]$SystemPrompt, [array]$History, [string]$Question, [bool]$IsPrivate = $false)
    $apiKey = [string]$script:Config.groqApiKey
    $model = [string]$script:Config.groqModel
    if ([string]::IsNullOrWhiteSpace($model)) { $model = "llama-3.3-70b-versatile" }

    $messages = @(@{ role = "system"; content = $SystemPrompt })
    foreach ($item in $History) {
        if ($item -is [System.Collections.IDictionary] -and $item.Contains("role") -and $item.Contains("content")) {
            $messages += @{ role = [string]$item["role"]; content = [string]$item["content"] }
        }
    }
    $messages += @{ role = "user"; content = $Question }

    $maxTokens = if ($IsPrivate) { 250 } else { 120 }
    $bodyObj = @{ model = $model; messages = $messages; max_tokens = $maxTokens; temperature = 0.5 }
    $jsonStr = $bodyObj | ConvertTo-Json -Depth 20
    $bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($jsonStr)

    $uri = "https://api.groq.com/openai/v1/chat/completions"
    $req = [System.Net.HttpWebRequest]::Create($uri)
    $req.Method = "POST"
    $req.Timeout = 30000
    $req.ContentType = "application/json; charset=utf-8"
    $req.Headers.Add("Authorization", "Bearer $apiKey")
    $req.ContentLength = $bodyBytes.Length

    $stream = $req.GetRequestStream()
    $stream.Write($bodyBytes, 0, $bodyBytes.Length)
    $stream.Close()

    $resp = $req.GetResponse()
    $reader = New-Object System.IO.StreamReader($resp.GetResponseStream(), [System.Text.Encoding]::UTF8)
    $respStr = $reader.ReadToEnd()
    $reader.Close()
    $resp.Close()

    if ([string]::IsNullOrWhiteSpace($respStr)) { return "" }
    $parsed = $respStr | ConvertFrom-Json
    if ($parsed.choices -and $parsed.choices.Count -gt 0 -and $parsed.choices[0].message) {
        return [string]$parsed.choices[0].message.content
    }
    return ""
}

function Get-SmartReply {
    param([string]$Text)
    if ([string]::IsNullOrWhiteSpace($Text)) { return $null }
    $lower = $Text.Trim().ToLowerInvariant()

    foreach ($entry in $script:SmartReplies) {
        foreach ($pattern in $entry.patterns) {
            if ($lower -match [regex]::Escape($pattern)) {
                return Get-RandomItem $entry.replies
            }
        }
    }
    return $null
}

function Get-AIReply {
    param([Int64]$ChatId, [Int64]$UserId, [string]$Question, [bool]$IsPrivate = $false)
    if (-not [bool]$script:Config.aiEnabled) { return "" }

    $smart = Get-SmartReply $Question
    if (-not [string]::IsNullOrWhiteSpace($smart)) {
        return $smart
    }

    $sysPrompt = if ($IsPrivate) {
        @"
You are Zirak (زیرەک), an exceptionally smart, polite, helpful, and knowledgeable AI assistant in private chat on Telegram.
You speak fluently in natural, beautiful, warm Sorani Kurdish (کوردیی سۆرانی ئاسایی و بەڕێز).

Strict Rules for Private Chat:
1. Answer any question (educational, general knowledge, technical, social, daily advice) intelligently, clearly, and helpfully.
2. Maintain a warm, friendly, respectful tone (گیان, بەڕێزم, کاکە, خوشکم).
3. Always respond in natural Sorani Kurdish without literal translation mistakes.
4. Keep answers concise, informative, and direct.
"@
    } else {
        @"
You are Zirak (زیرەک), a friendly, intelligent young Kurdish guy in a Telegram group chat.
You speak only in short, natural, human Sorani Kurdish (کوردیی سۆرانی ئاسایی چات).

Strict Rules:
1. NEVER translate machine English into Kurdish. Never use broken literal dictionary words.
2. Respond in 1 short, natural sentence as a real Kurdish friend in chat.
3. Use everyday Kurdish chat phrases (وەڵا, گیان, کاکە, ئاساییە, عافیەت بێت, هههه).
4. Be witty, friendly, and respectful.
"@
    }

    $answer = ""
    if (-not [string]::IsNullOrWhiteSpace($script:Config.groqApiKey)) {
        try {
            $answer = Invoke-GroqReply $sysPrompt @() $Question $IsPrivate
            $answer = Invoke-CleanAIAnswer $answer
        } catch {
            Write-Warning "Groq: $($_.Exception.Message)"
            $answer = ""
        }
    }

    if ([string]::IsNullOrWhiteSpace($answer)) {
        return "گیان لە خزمەتتم، دەتوانیت دووبارە ڕوونی بکەیتەوە؟ 🌸"
    }

    return $answer
}

# ═══════════════════════════════════════════════════════════════════════════════
#  بەشی ٥: فیلتەرەکانی ئاسایش (Smart Moderation Core)
# ═══════════════════════════════════════════════════════════════════════════════

function Test-ContainsBadWord {
    param([string]$Text)
    if ([string]::IsNullOrWhiteSpace($Text)) { return $false }
    $cleanText = $Text.ToLowerInvariant()
    
    foreach ($p in $script:BadWordsList) {
        if ($cleanText.Contains($p.ToLowerInvariant())) { return $true }
    }

    foreach ($phrase in $script:BadPhrasesList) {
        if ($cleanText -match $phrase) { return $true }
    }

    return $false
}

function Test-ContainsLinkOrSpam {
    param([hashtable]$Msg, [string]$Text)

    if (-not [string]::IsNullOrWhiteSpace($Text)) {
        if ($Text -match '(?i)\bhttps?://|\bt\.me/|\btelegram\.me/|\bwww\.|@[a-zA-Z0-9_]{4,}') {
            return $true
        }
    }

    if ($Msg.ContainsKey("entities") -and $null -ne $Msg["entities"]) {
        foreach ($e in $Msg["entities"]) {
            $type = [string]$e["type"]
            if ($type -eq "url" -or $type -eq "text_link" -or $type -eq "mention") {
                return $true
            }
        }
    }

    if ($Msg.ContainsKey("caption_entities") -and $null -ne $Msg["caption_entities"]) {
        foreach ($e in $Msg["caption_entities"]) {
            $type = [string]$e["type"]
            if ($type -eq "url" -or $type -eq "text_link" -or $type -eq "mention") {
                return $true
            }
        }
    }

    if ($Msg.ContainsKey("reply_markup")) {
        return $true
    }

    if ($Msg.ContainsKey("forward_date") -or $Msg.ContainsKey("forward_from") -or $Msg.ContainsKey("forward_from_chat") -or $Msg.ContainsKey("forward_sender_name")) {
        return $true
    }

    return $false
}

# ═══════════════════════════════════════════════════════════════════════════════
#  بەشی ٧: بەڕێوەبردنی پەیامەکان (Message Processor & Security Core)
# ═══════════════════════════════════════════════════════════════════════════════

function Invoke-HandleMessage {
    param([hashtable]$Message)
    if (-not $Message.ContainsKey("chat") -or -not $Message.ContainsKey("from")) { return }
    $chat = $Message["chat"]
    $chatType = $chat["type"]
    if ($chatType -ne "group" -and $chatType -ne "supergroup" -and $chatType -ne "private") { return }
    $chatId = [Int64]$chat["id"]
    $msgId = [int]$Message["message_id"]
    $from = $Message["from"]
    $userId = [Int64]$from["id"]
    $displayName = Get-DisplayName $from

    if ($Message.ContainsKey("new_chat_members")) {
        foreach ($member in $Message["new_chat_members"]) {
            if ($member.ContainsKey("is_bot") -and $member["is_bot"]) { continue }
            $mName = Get-DisplayName $member
            $wMsg = (Get-RandomItem $script:WelcomeMessages).Replace("{name}", $mName)
            Send-TgMessage $chatId $wMsg $msgId
        }
    }

    $text = ""
    if ($Message.ContainsKey("text")) { $text = [string]$Message["text"] }
    elseif ($Message.ContainsKey("caption")) { $text = [string]$Message["caption"] }

    # 💬 ۱. چاتی شەخسی (Private Chat) - وەڵامدانەوەی زیرەکانەی هەموو پرسیارێک بە کوردی
    if ($chatType -eq "private") {
        if (-not [string]::IsNullOrWhiteSpace($text)) {
            $reply = Get-AIReply $chatId $userId $text -IsPrivate $true
            if (-not [string]::IsNullOrWhiteSpace($reply)) { Send-TgMessage $chatId $reply $msgId }
        }
        return
    }

    # 🛡️ ۲. ئاسایشی توندی گروپ (Security Rules for Non-Admins)
    $isAdmin = Test-IsAdmin $chatId $userId

    if (-not $isAdmin) {
        $violationReason = ""

        if ([bool]$script:Config.blockPhotos -and $Message.ContainsKey("photo")) {
            $violationReason = "ناردنی وێنە 📷"
        }
        elseif ([bool]$script:Config.blockVideos -and ($Message.ContainsKey("video") -or $Message.ContainsKey("video_note"))) {
            $violationReason = "ناردنی ڤیدیۆ 🎥"
        }
        elseif ([bool]$script:Config.blockGIFs -and ($Message.ContainsKey("animation") -or $Message.ContainsKey("document"))) {
            $violationReason = "ناردنی GIF / فۆرمات / فایل 🎬"
        }
        elseif ([bool]$script:Config.blockStickers -and $Message.ContainsKey("sticker")) {
            $violationReason = "ناردنی ستیکەر 🎭"
        }
        elseif ($Message.ContainsKey("voice") -or $Message.ContainsKey("audio")) {
            $violationReason = "ناردنی فایلی دەنگی 🎙️"
        }
        elseif ([bool]$script:Config.blockLinks -and (Test-ContainsLinkOrSpam $Message $text)) {
            $violationReason = "ناردنی لینک، پۆست یان ریپڵای دوگمەدار 🔗"
        }
        elseif ([bool]$script:Config.blockBadWords -and (Test-ContainsBadWord $text)) {
            $violationReason = "قسەی ناشرین و جنێو 🤬"
        }

        if (-not [string]::IsNullOrWhiteSpace($violationReason)) {
            Remove-TgMessage $chatId $msgId
            $cnt = Add-UserWarning $chatId $userId
            Send-TgMessage $chatId "⚠️ $displayName $violationReason قەدەغەیە! ئاگاداری: ($cnt/$($script:Config.maxWarnings))"
            
            if ($cnt -ge [int]$script:Config.maxWarnings) {
                Set-UserMute $chatId $userId 60
                Send-TgMessage $chatId "🚫 $displayName بەهۆی دووبارەکردنەوەی سەرپێچی، بۆ ماوەی ١ کاتژمێر لە چاتکردن بێدەنگ کرا!"
            }
            return
        }
    }

    # 💬 ۳. وەڵامدانەوەی AI لە گروپدا
    if (-not [string]::IsNullOrWhiteSpace($text)) {
        $shouldAiReply = $true

        if ($Message.ContainsKey("reply_to_message") -and $null -ne $Message["reply_to_message"]) {
            $repTarget = $Message["reply_to_message"]
            if ($repTarget.ContainsKey("from") -and $null -ne $repTarget["from"]) {
                $targetUser = $repTarget["from"]
                $targetId = [Int64]$targetUser["id"]
                $isTargetBot = [bool]($targetUser.ContainsKey("is_bot") -and $targetUser["is_bot"])

                if ($targetId -ne $script:BotId -and -not $isTargetBot) {
                    $shouldAiReply = $false
                }
            }
        }

        if ($shouldAiReply) {
            $reply = Get-AIReply $chatId $userId $text -IsPrivate $false
            if (-not [string]::IsNullOrWhiteSpace($reply)) {
                Send-TgMessage $chatId $reply $msgId
            }
        }
    }
}

Invoke-Telegram "deleteWebhook" @{ drop_pending_updates = $true } | Out-Null

$offset = 0
while ($true) {
    try {
        $response = Invoke-Telegram "getUpdates" @{ offset = $offset; timeout = 30 }
        if ($null -eq $response -or -not $response.ok) { Start-Sleep -Seconds 3; continue }
        foreach ($update in $response.result) {
            $updateHash = ConvertTo-Hashtable $update
            $offset = [int]$updateHash["update_id"] + 1
            if ($updateHash.ContainsKey("message")) {
                try { Invoke-HandleMessage $updateHash["message"] }
                catch { Write-Warning "Error: $($_.Exception.Message)" }
            }
        }
    } catch {
        Write-Warning "Loop: $($_.Exception.Message)"
        Start-Sleep -Seconds 5
    }
}
