---
name: wechat-agent-report
description: Use when sending a task completion report, status update, or summary to a configured WeChat agent conversation (such as a daily summary agent), or when the user asks to notify, report to, or sync with a WeChat agent.
---

# WeChat Agent Report

## Overview

Type a formatted report into a named WeChat agent conversation by driving the WeChat desktop UI. The message is sent as the user, so the agent on the other side receives it and can include it in later summaries. Works on macOS and Windows.

## When to Use

- The user asks to notify a WeChat agent that a task is done
- You finished work that a configured agent should record
- The user says "发给每日总结" / "report to the agent"

Do NOT use this for ordinary people or group chats.

## Quick Reference

```bash
python3 ~/.claude/skills/wechat-agent-report/scripts/send_report.py --list

python3 ~/.claude/skills/wechat-agent-report/scripts/send_report.py \
  --agent daily-summary \
  --title "完成登录页重构" \
  --summary "重构了表单校验和错误提示，补充 6 个单元测试，已合并到 main。" \
  --special "下次优先处理移动端适配"
```

- `--special` is optional.
- `--summary` is limited by the agent's `max_words` (default 200); the script truncates and warns.
- Time is filled as `「YYYY-MM-DD HH:MM」`.

## Configuration

`~/.claude/wechat-agent-report/config.json`

```json
{
  "agents": {
    "daily-summary": {
      "wechat_name": "每日总结 Agent",
      "max_words": 200,
      "reference": "references/daily-summary.md"
    }
  }
}
```

- `wechat_name`: the conversation name exactly as shown in WeChat search.
- `reference`: submission template, resolved relative to the config directory.
- Adding an agent: create `references/<agent>.md`, add an entry here.

## Agent Templates

Templates live in `~/.claude/wechat-agent-report/references/`. Placeholders: `{title}`, `{summary}`, `{special}`, `{time}`. A line containing only `{special}` is dropped when no special note is given.

daily-summary:

```
【{title}】
{summary}
<特别说明>{special}
「{time}」
```

## How Sending Works

1. Builds the message from the agent's template.
2. Activates WeChat, searches `wechat_name`, opens the first result.
3. Pastes the message into the input box and presses Enter.

macOS uses AppleScript; Windows uses PowerShell SendKeys. Both briefly take keyboard focus.

## Requirements

- WeChat desktop client logged in, with the agent conversation visible in search
- macOS: Accessibility permission for the terminal/Claude
- Windows: PowerShell 5+, WeChat desktop client
- Do not type or click while the script is running

## Common Mistakes

| Mistake | Fix |
|---|---|
| Wrong conversation opened | Use the exact `wechat_name` from WeChat search |
| Text sent to the wrong window | The script activates WeChat; do not steal focus mid-run |
| Summary truncated | Shorten it or raise `max_words` |
| Special note missing | It is optional; omit `--special` |

## Deployment

macOS / Linux:

```bash
git clone https://github.com/liuchunyi-buaa/wechat-agent-report-skill.git
cd wechat-agent-report-skill
bash install.sh
# then edit ~/.claude/wechat-agent-report/config.json
```

Windows (PowerShell):

```powershell
git clone https://github.com/liuchunyi-buaa/wechat-agent-report-skill.git
cd wechat-agent-report-skill
powershell -ExecutionPolicy Bypass -File install.ps1
# then edit %USERPROFILE%\.claude\wechat-agent-report\config.json
```
