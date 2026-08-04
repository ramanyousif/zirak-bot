param(
    [string]$ConfigPath = ".\config.json"
)

$ErrorActionPreference = "Stop"
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

function Ensure-Map {
    param([hashtable]$Map, [string]$Key)
    if ($null -eq $Map) { return $null }
    if (-not $Map.ContainsKey($Key) -or $null -eq $Map[$Key]) { $Map[$Key] = @{} }
    return $Map[$Key]
}

function Get-UnixTime { return [int][DateTimeOffset]::UtcNow.ToUnixTimeSeconds() }

$Config = @{
    token = $env:TELEGRAM_BOT_TOKEN
    botUsername = "mygrouppatwmat_bot"
    aiProvider = "ollama"
    ollamaBaseUrl = "http://127.0.0.1:11434"
    ollamaApiPath = "/api/chat"
    ollamaModel = "llama3.2"
    aiEnabled = $true
    aiInPrivateChats = $true
    aiInGroupsOnlyWhenMentioned = $true
    aiHistoryMessages = 8
    aiSystemPrompt = "You are a helpful Telegram assistant. Reply briefly, politely, and in Kurdish Sorani when possible."
    deleteLinks = $true
    floodLimit = 5
    floodWindowSeconds = 10
    maxWarnings = 3
    autoMuteMinutes = 60
    welcomeMessage = "Welcome {name}. Please read the group rules."
}

if (Test-Path -LiteralPath $ConfigPath) {
    $fileConfig = Read-JsonFile $ConfigPath
    foreach ($key in $fileConfig.Keys) { $Config[$key] = $fileConfig[$key] }
}

if ([string]::IsNullOrWhiteSpace($Config.token) -or $Config.token -eq "PUT_YOUR_BOTFATHER_TOKEN_HERE") {
    throw "Telegram bot token is missing. Set TELEGRAM_BOT_TOKEN or configure config.json."
}

$ApiBase = "https://api.telegram.org/bot$($Config.token)"
$StatePath = ".\data\state.json"
$State = Read-JsonFile $StatePath
if (-not $State.ContainsKey("chats")) { $State["chats"] = @{} }
if (-not $State.ContainsKey("warnings")) { $State["warnings"] = @{} }
if (-not $State.ContainsKey("flood")) { $State["flood"] = @{} }
if (-not $State.ContainsKey("aiHistory")) { $State["aiHistory"] = @{} }

function Save-State { Write-JsonFile $StatePath $script:State }

function Invoke-Telegram {
    param([string]$Method, [hashtable]$Body = @{})
    $uri = "$script:ApiBase/$Method"
    try {
        return Invoke-RestMethod -Uri $uri -Method Post -ContentType "application/json; charset=utf-8" -Body ($Body | ConvertTo-Json -Depth 20)
    }
    catch {
        Write-Warning "Telegram API error"
        return $null
    }
}

function Send-Message {
    param([Int64]$ChatId, [string]$Text, [int]$ReplyTo = 0)
    $body = @{ chat_id = $ChatId; text = $Text; disable_web_page_preview = $true }
    if ($ReplyTo -gt 0) { $body["reply_to_message_id"] = $ReplyTo; $body["allow_sending_without_reply"] = $true }
    Invoke-Telegram "sendMessage" $body | Out-Null
}

function Get-AIReply {
    param([Int64]$ChatId, [Int64]$UserId, [string]$DisplayName, [string]$Question)
    if (-not [bool]$script:Config.aiEnabled) { return "" }
    $historyKey = "$ChatId`:$UserId"
    if (-not $script:State["aiHistory"].ContainsKey($historyKey)) { $script:State["aiHistory"][$historyKey] = @() }

    $messages = @(@{ role = "system"; content = [string]$script:Config.aiSystemPrompt })
    foreach ($item in @($script:State["aiHistory"][$historyKey])) {
        $messages += @{ role = [string]$item["role"]; content = [string]$item["content"] }
    }
    $messages += @{ role = "user"; content = "${DisplayName}: $Question" }

    try {
        $body = @{ model = [string]$script:Config.ollamaModel; messages = $messages; stream = $false }
        $ollamaBaseUrl = ([string]$script:Config.ollamaBaseUrl).TrimEnd("/")
        $apiPath = [string]$script:Config.ollamaApiPath
        if ([string]::IsNullOrWhiteSpace($apiPath)) { $apiPath = "/api/chat" }
        $ollamaUri = "$ollamaBaseUrl$apiPath"
        $response = Invoke-RestMethod -Uri $ollamaUri -Method Post -ContentType "application/json; charset=utf-8" -Body ($body | ConvertTo-Json -Depth 20)
        $answer = ""
        if ($response -and $response.message -and $response.message.content) { $answer = [string]$response.message.content }
        elseif ($response -and $response.response) { $answer = [string]$response.response }
        if ([string]::IsNullOrWhiteSpace($answer)) { return "Sorry, I could not prepare a useful reply right now." }

        $script:State["aiHistory"][$historyKey] += @(
            @{ role = "user"; content = $Question },
            @{ role = "assistant"; content = $answer }
        )
        $maxItems = [Math]::Max(2, [int]$script:Config.aiHistoryMessages)
        $history = @($script:State["aiHistory"][$historyKey])
        if ($history.Count -gt $maxItems) { $script:State["aiHistory"][$historyKey] = @($history | Select-Object -Last $maxItems) }
        Save-State
        return $answer
    }
    catch {
        Write-Warning "Ollama API error"
        return "Sorry, I could not reach Ollama."
    }
}

function Get-BotUsername { param([hashtable]$Config) $username = [string]$Config.botUsername; if ([string]::IsNullOrWhiteSpace($username)) { $username = "mygrouppatwmat_bot" }; return $username.ToLowerInvariant() }

function Get-AIQuestion {
    param([hashtable]$Message, [string]$Text, [string]$BotUsername)
    $trimmed = $Text.Trim()
    if ($trimmed -match '^/ai(?:@[^\s]+)?(?:\s+(.+))?$') { return [string]$Matches[1] }
    $escapedUsername = [regex]::Escape($BotUsername)
    if ($trimmed -match "(?i)(?:^|\s)@?$escapedUsername\s*(.*)$") { return ([string]$Matches[1]).Trim() }
    if ($Message.ContainsKey("reply_to_message") -and $Message["reply_to_message"].ContainsKey("from")) {
        $repliedFrom = $Message["reply_to_message"]["from"]
        if ($repliedFrom.ContainsKey("username") -and ([string]$repliedFrom["username"]).ToLowerInvariant() -eq $BotUsername) { return $trimmed }
    }
    return ""
}

function Delete-Message { param([Int64]$ChatId, [int]$MessageId) Invoke-Telegram "deleteMessage" @{ chat_id = $ChatId; message_id = $MessageId } | Out-Null }

function Get-DisplayName { param([hashtable]$User) if (-not [string]::IsNullOrWhiteSpace($User["first_name"])) { return $User["first_name"] }; if (-not [string]::IsNullOrWhiteSpace($User["username"])) { return "@$($User["username"])" }; return [string]$User["id"] }

function Test-Admin {
    param([Int64]$ChatId, [Int64]$UserId)
    $response = Invoke-Telegram "getChatMember" @{ chat_id = $ChatId; user_id = $UserId }
    if ($null -eq $response -or -not $response.ok) { return $false }
    $status = $response.result.status
    return ($status -eq "creator" -or $status -eq "administrator")
}

function Get-ChatSettings {
    param([Int64]$ChatId)
    $chatKey = [string]$ChatId
    $chat = Ensure-Map $script:State["chats"] $chatKey
    if (-not $chat.ContainsKey("rules")) { $chat["rules"] = "Group rules not set yet." }
    return $chat
}

function Add-Warning { param([Int64]$ChatId, [Int64]$UserId) $chatWarnings = Ensure-Map $script:State["warnings"] ([string]$ChatId); $key = [string]$UserId; if (-not $chatWarnings.ContainsKey($key)) { $chatWarnings[$key] = 0 }; $chatWarnings[$key] = [int]$chatWarnings[$key] + 1; Save-State; return [int]$chatWarnings[$key] }

function Get-WarningCount { param([Int64]$ChatId, [Int64]$UserId) $chatKey = [string]$ChatId; $userKey = [string]$UserId; if (-not $script:State["warnings"].ContainsKey($chatKey)) { return 0 }; if (-not $script:State["warnings"][$chatKey].ContainsKey($userKey)) { return 0 }; return [int]$script:State["warnings"][$chatKey][$userKey] }

function Mute-User { param([Int64]$ChatId, [Int64]$UserId, [int]$Minutes) $until = (Get-UnixTime) + ($Minutes * 60); Invoke-Telegram "restrictChatMember" @{ chat_id = $ChatId; user_id = $UserId; until_date = $until; permissions = @{ can_send_messages = $false; can_send_audios = $false; can_send_documents = $false; can_send_photos = $false; can_send_videos = $false; can_send_video_notes = $false; can_send_voice_notes = $false; can_send_polls = $false; can_send_other_messages = $false; can_add_web_page_previews = $false; can_change_info = $false; can_invite_users = $false; can_pin_messages = $false; can_manage_topics = $false } } | Out-Null }

function Ban-User { param([Int64]$ChatId, [Int64]$UserId) Invoke-Telegram "banChatMember" @{ chat_id = $ChatId; user_id = $UserId } | Out-Null }

function Unban-User { param([Int64]$ChatId, [Int64]$UserId) Invoke-Telegram "unbanChatMember" @{ chat_id = $ChatId; user_id = $UserId; only_if_banned = $true } | Out-Null }

function Has-Link { param([string]$Text) if ([string]::IsNullOrWhiteSpace($Text)) { return $false }; return ($Text -match '(?i)\bhttps?://|\bt\.me/|\btelegram\.me/|\bwww\.|@[a-zA-Z0-9_]{5,}') }

function Test-Flood { param([Int64]$ChatId, [Int64]$UserId) $key = "$ChatId`:$UserId"; $now = Get-UnixTime; $windowStart = $now - [int]$script:Config.floodWindowSeconds; if (-not $script:State["flood"].ContainsKey($key)) { $script:State["flood"][$key] = @() }; $recent = @(); foreach ($timestamp in $script:State["flood"][$key]) { if ([int]$timestamp -ge $windowStart) { $recent += [int]$timestamp } }; $recent += $now; $script:State["flood"][$key] = $recent; return ($recent.Count -gt [int]$script:Config.floodLimit) }

function Parse-DurationMinutes { param([string]$Value) if ([string]::IsNullOrWhiteSpace($Value)) { return 10 }; if ($Value -match '^(\d+)(m|h|d)?$') { $amount = [int]$Matches[1]; $unit = $Matches[2]; switch ($unit) { 'h' { return $amount * 60 }; 'd' { return $amount * 1440 }; default { return $amount } } }; return 10 }

function Get-ReplyUser { param([hashtable]$Message) if (-not $Message.ContainsKey("reply_to_message")) { return $null }; if (-not $Message["reply_to_message"].ContainsKey("from")) { return $null }; return $Message["reply_to_message"]["from"] }

function Handle-Command { param([hashtable]$Message, [string]$Text) $chatId = [Int64]$Message["chat"]["id"]; $messageId = [int]$Message["message_id"]; $from = $Message["from"]; $userId = [Int64]$from["id"]; $commandParts = $Text.Trim().Split(" ", 2, [System.StringSplitOptions]::RemoveEmptyEntries); $command = $commandParts[0].Split("@")[0].ToLowerInvariant(); $argument = ""; if ($commandParts.Count -gt 1) { $argument = $commandParts[1] }; switch ($command) { "/start" { Send-Message $chatId "Hello! I am the group protection bot. Send /help for commands." $messageId }; "/help" { $helpText = @"
Commands:
/id - chat id
/rules - view rules
/setrules text - set rules, admin only
/warn - warn by reply
/warnings - view warnings by reply
/mute 10m - mute by reply
/ban - ban by reply
/unban user_id - unban
/ai question - ask Ollama
"@; Send-Message $chatId $helpText $messageId }; "/id" { Send-Message $chatId "Chat ID: $chatId" $messageId }; "/rules" { $chat = Get-ChatSettings $chatId; Send-Message $chatId $chat["rules"] $messageId }; "/setrules" { if (-not (Test-Admin $chatId $userId)) { Send-Message $chatId "Only admins can set the rules." $messageId; return }; if ([string]::IsNullOrWhiteSpace($argument)) { Send-Message $chatId "Example: /setrules Respect others and do not share links." $messageId; return }; $chat = Get-ChatSettings $chatId; $chat["rules"] = $argument; Save-State; Send-Message $chatId "Rules saved." $messageId }; "/warn" { if (-not (Test-Admin $chatId $userId)) { Send-Message $chatId "Only admins can warn users." $messageId; return }; $target = Get-ReplyUser $Message; if ($null -eq $target) { Send-Message $chatId "Please reply to the user you want to warn." $messageId; return }; $count = Add-Warning $chatId ([Int64]$target["id"]); Send-Message $chatId "$(Get-DisplayName $target) was warned. Warnings: $count/$($script:Config.maxWarnings)" $messageId; if ($count -ge [int]$script:Config.maxWarnings) { Mute-User $chatId ([Int64]$target["id"]) ([int]$script:Config.autoMuteMinutes); Send-Message $chatId "Muted for $($script:Config.autoMuteMinutes) minutes due to repeated warnings." $messageId } }; "/warnings" { $target = Get-ReplyUser $Message; if ($null -eq $target) { Send-Message $chatId "Reply to a user to see their warnings." $messageId; return }; $count = Get-WarningCount $chatId ([Int64]$target["id"]); Send-Message $chatId "$(Get-DisplayName $target): $count warnings" $messageId }; "/mute" { if (-not (Test-Admin $chatId $userId)) { Send-Message $chatId "Only admins can mute users." $messageId; return }; $target = Get-ReplyUser $Message; if ($null -eq $target) { Send-Message $chatId "Reply to the user you want to mute." $messageId; return }; $minutes = Parse-DurationMinutes $argument; Mute-User $chatId ([Int64]$target["id"]) $minutes; Send-Message $chatId "$(Get-DisplayName $target) muted for $minutes minutes." $messageId }; "/ban" { if (-not (Test-Admin $chatId $userId)) { Send-Message $chatId "Only admins can ban users." $messageId; return }; $target = Get-ReplyUser $Message; if ($null -eq $target) { Send-Message $chatId "Reply to the user you want to ban." $messageId; return }; Ban-User $chatId ([Int64]$target["id"]); Send-Message $chatId "$(Get-DisplayName $target) was banned." $messageId }; "/unban" { if (-not (Test-Admin $chatId $userId)) { Send-Message $chatId "Only admins can unban users." $messageId; return }; if ($argument -notmatch '^\d+$') { Send-Message $chatId "Example: /unban 123456789" $messageId; return }; Unban-User $chatId ([Int64]$argument); Send-Message $chatId "Unbanned: $argument" $messageId } } }

function Handle-Message {
    param([hashtable]$Message)
    if (-not $Message.ContainsKey("chat") -or -not $Message.ContainsKey("from")) { return }
    $chat = $Message["chat"]
    $chatType = $chat["type"]
    if ($chatType -ne "group" -and $chatType -ne "supergroup" -and $chatType -ne "private") { return }
    $chatId = [Int64]$chat["id"]
    $messageId = [int]$Message["message_id"]
    $from = $Message["from"]
    $userId = [Int64]$from["id"]
    if ($Message.ContainsKey("new_chat_members")) {
        foreach ($member in $Message["new_chat_members"]) {
            if ($member.ContainsKey("is_bot") -and $member["is_bot"]) { continue }
            $name = Get-DisplayName $member
            $welcome = ([string]$script:Config.welcomeMessage).Replace("{name}", $name)
            Send-Message $chatId $welcome $messageId
        }
    }
    $text = ""
    if ($Message.ContainsKey("text")) { $text = [string]$Message["text"] }
    elseif ($Message.ContainsKey("caption")) { $text = [string]$Message["caption"] }
    if ($text.StartsWith("/")) {
        if ($text -match '^/ai(?:@[^\s]+)?(?:\s+.+)?$') {
            $question = Get-AIQuestion $Message $text (Get-BotUsername $script:Config)
            if ([string]::IsNullOrWhiteSpace($question)) { Send-Message $chatId "Example: /ai how are you?" $messageId; return }
            $reply = Get-AIReply $chatId $userId (Get-DisplayName $from) $question
            Send-Message $chatId $reply $messageId
            return
        }
        Handle-Command $Message $text
        return
    }
    if ($chatType -eq "private") {
        if ([bool]$script:Config.aiInPrivateChats -and -not [string]::IsNullOrWhiteSpace($text)) {
            $reply = Get-AIReply $chatId $userId (Get-DisplayName $from) $text
            Send-Message $chatId $reply $messageId
        }
        return
    }
    $botUsername = Get-BotUsername $script:Config
    $aiQuestion = Get-AIQuestion $Message $text $botUsername
    $shouldAnswerAi = -not [string]::IsNullOrWhiteSpace($aiQuestion)
    if (-not $shouldAnswerAi -and -not [bool]$script:Config.aiInGroupsOnlyWhenMentioned) { $shouldAnswerAi = -not [string]::IsNullOrWhiteSpace($text) }
    if ($shouldAnswerAi) {
        $reply = Get-AIReply $chatId $userId (Get-DisplayName $from) $(if ($aiQuestion) { $aiQuestion } else { $text })
        Send-Message $chatId $reply $messageId
        return
    }
    $isAdmin = Test-Admin $chatId $userId
    if (-not $isAdmin -and [bool]$script:Config.deleteLinks -and (Has-Link $text)) { Delete-Message $chatId $messageId; $count = Add-Warning $chatId $userId; Send-Message $chatId "$(Get-DisplayName $from), links are not allowed. Warnings: $count/$($script:Config.maxWarnings)"; if ($count -ge [int]$script:Config.maxWarnings) { Mute-User $chatId $userId ([int]$script:Config.autoMuteMinutes); Send-Message $chatId "Muted for $($script:Config.autoMuteMinutes) minutes because of repeated violations." }; return }
    if (-not $isAdmin -and (Test-Flood $chatId $userId)) { Delete-Message $chatId $messageId; $count = Add-Warning $chatId $userId; Send-Message $chatId "$(Get-DisplayName $from), please do not spam. Warnings: $count/$($script:Config.maxWarnings)"; if ($count -ge [int]$script:Config.maxWarnings) { Mute-User $chatId $userId ([int]$script:Config.autoMuteMinutes); Send-Message $chatId "Muted for $($script:Config.autoMuteMinutes) minutes because of spam." }; Save-State }
}

Write-Host "Starting Telegram group protection bot..."
Write-Host "Bot username: $(Get-BotUsername $Config)"
Write-Host "Using Ollama at $($Config.ollamaBaseUrl) with model $($Config.ollamaModel)"
Write-Host "Press Ctrl+C to stop."

$offset = 0
while ($true) {
    $response = Invoke-Telegram "getUpdates" @{ offset = $offset; timeout = 30; allowed_updates = @("message") }
    if ($null -eq $response -or -not $response.ok) { Start-Sleep -Seconds 3; continue }
    foreach ($update in $response.result) {
        $updateHash = ConvertTo-Hashtable $update
        $offset = [int]$updateHash["update_id"] + 1
        if ($updateHash.ContainsKey("message")) {
            try { Handle-Message $updateHash["message"] }
            catch { Write-Warning "Update handling failed" }
        }
    }
}
