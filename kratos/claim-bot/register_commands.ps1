# PowerShell port of Bricked-Sorting kratos/claim-bot/register_commands.py.
# Registers the claim bot's slash commands in one Discord server. Run once, on your own PC:
#   powershell -ExecutionPolicy Bypass -File .\register_commands.ps1
# The bot token is typed hidden, used for this one call, never saved. Reset it in the portal afterwards.

$ErrorActionPreference = 'Stop'

$appId = (Read-Host 'Application ID (General Information)').Trim()
$guild = (Read-Host 'Server ID (right-click the server > Copy Server ID)').Trim()
if ($appId -notmatch '^\d+$' -or $guild -notmatch '^\d+$') { throw 'Application ID and Server ID must be numbers.' }
$secure = Read-Host 'Bot token (hidden)' -AsSecureString

# Same commands as register_commands.py
$commands = @'
[
  {"name": "tasks", "description": "List open tasks (or one status)",
   "options": [{"name": "status", "description": "Only this status", "type": 3, "required": false,
                "choices": [{"name": "to do", "value": "todo"}, {"name": "in progress", "value": "in_progress"},
                            {"name": "blocked", "value": "blocked"}, {"name": "done", "value": "done"}]}]},
  {"name": "mytasks", "description": "Your open tasks"},
  {"name": "claim", "description": "Take a task",
   "options": [{"name": "task", "description": "Task id, like identify-02", "type": 3, "required": true, "max_length": 40}]},
  {"name": "start", "description": "Mark your task in progress",
   "options": [{"name": "task", "description": "Task id, like identify-02", "type": 3, "required": true, "max_length": 40}]},
  {"name": "blocked", "description": "Mark your task blocked",
   "options": [{"name": "task", "description": "Task id, like identify-02", "type": 3, "required": true, "max_length": 40},
               {"name": "reason", "description": "What is blocking it", "type": 3, "required": true, "max_length": 200}]},
  {"name": "done", "description": "Mark your task done",
   "options": [{"name": "task", "description": "Task id, like identify-02", "type": 3, "required": true, "max_length": 40}]},
  {"name": "todo", "description": "Move your task back to to do",
   "options": [{"name": "task", "description": "Task id, like identify-02", "type": 3, "required": true, "max_length": 40}]},
  {"name": "release", "description": "Give up a task so someone else can claim it",
   "options": [{"name": "task", "description": "Task id, like identify-02", "type": 3, "required": true, "max_length": 40}]},
  {"name": "export", "description": "Branden only: live owners and statuses for tasks.json"}
]
'@

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try {
    $token = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr).Trim()
    $r = Invoke-RestMethod -Method Put `
        -Uri "https://discord.com/api/v10/applications/$appId/guilds/$guild/commands" `
        -Headers @{ Authorization = "Bot $token" } `
        -UserAgent 'DiscordBot (https://github.com/jerrekt/Bricked-Sorting, 1.0)' `
        -ContentType 'application/json' -Body ([Text.Encoding]::UTF8.GetBytes($commands)) -TimeoutSec 15
    'Registered: ' + (($r | ForEach-Object { '/' + $_.name }) -join ', ')
} catch {
    $msg = $_.Exception.Message
    if ($_.ErrorDetails.Message) { $msg += ' ' + $_.ErrorDetails.Message.Substring(0, [Math]::Min(300, $_.ErrorDetails.Message.Length)) }
    Write-Host "Discord said: $msg" -ForegroundColor Red
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    Remove-Variable token, secure -ErrorAction SilentlyContinue
}
'Now reset the bot token in the portal (Bot > Reset Token) and do not save the new one.'
