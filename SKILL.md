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
python ~/.claude/skills/wechat-agent-report/scripts/send_report.py --list

python ~/.claude/skills/wechat-agent-report/scripts/send_report.py \
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

Templates live in `~/.claude/wechat-agent-report/references/`. Placeholders: `{title}`, `{summary}`, `{special}`, `{time}`, `{device}`. A line containing only `{special}` is dropped when no special note is given. `{device}` is the submitting machine's hostname.

daily-summary:

```
【{title}】
{summary}
<特别说明>{special}
「{time}」
「{device}」
```

## How Sending Works

1. Builds the message from the agent's template.
2. Brings WeChat to the front, searches `wechat_name`, screenshots the window
   region, and OCRs the result list.
3. Clicks the row containing "微信 ClawBot" (the real conversation, not a
   search suggestion). On Windows the opened chat title is verified before
   anything is sent.
4. Pastes the message into the input box and presses Enter.

macOS uses AppleScript + Vision OCR (`find_and_click.swift`). Windows uses the
same screenshot-and-OCR approach inside `send_report.py` (Windows OCR +
Pillow); PowerShell is not used at runtime. Both briefly take keyboard focus.

Use `--dry-run` to locate the conversation and fill in the message without
pressing Enter.

## Requirements

- WeChat desktop client logged in, with the agent conversation visible in search
- macOS: Accessibility permission for the terminal/Claude
- Windows: Python 3, `pip install winsdk pillow`, and a Chinese OCR language
  pack, plus the WeChat 4.x desktop client
- Do not type, click, or resize the WeChat window while the script is running

## Common Mistakes

| Mistake | Fix |
|---|---|
| Wrong conversation opened | Use the exact `wechat_name` from WeChat search |
| Text sent to the wrong window | The script activates WeChat; do not steal focus mid-run |
| "缺少依赖" on Windows | Run `pip install winsdk pillow` |
| "在搜索结果中找不到对话" | Make sure WeChat is not being resized while it runs |
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
python -m pip install winsdk pillow
# then edit %USERPROFILE%\.claude\wechat-agent-report\config.json
```

`install.ps1` only copies files; sending itself runs in Python and does not
use PowerShell.
