---
name: wechat-agent-report
description: Use when sending a task completion report, status update, or summary to a configured WeChat agent conversation (such as a daily summary agent) via ClawBot, or when the user asks to notify, report to, or sync with a WeChat agent.
---

# WeChat Agent Report

## Overview

Send a formatted completion report to a named WeChat agent conversation through the ClawBot API. Each agent has its own ClawBot credentials and submission format, so the same skill works for any number of agent conversations.

## When to Use

- The user asks to notify a WeChat agent that a task is done
- You finished work that a configured agent should record (daily summary, project tracker, etc.)
- The user says "发给每日总结" / "report to the agent"

Do NOT use this to message ordinary people or group chats.

## Quick Reference

```bash
# List configured agents
python3 ~/.claude/skills/wechat-agent-report/scripts/send_report.py --list

# Send a report
python3 ~/.claude/skills/wechat-agent-report/scripts/send_report.py \
  --agent daily-summary \
  --title "完成登录页重构" \
  --summary "重构了登录页的表单校验和错误提示，补充了 6 个单元测试，已合并到 main。" \
  --special "下次优先处理移动端适配"
```

- `--special` is optional; omit it when there is no special instruction.
- `--summary` must be within the agent's `max_words` (default 200); the script truncates and warns.
- Time is filled automatically as `「YYYY-MM-DD HH:MM」`.

## Configuration

Global config: `~/.claude/wechat-agent-report/config.json`

```json
{
  "agents": {
    "daily-summary": {
      "clawbot_dir": "/Users/liuchunyi/study/notification/clawbot",
      "max_words": 200,
      "format": "【{title}】\n{summary}\n{special}\n「{time}」"
    }
  }
}
```

- `clawbot_dir`: directory containing `clawbot.py`, `credentials.json`, `context.json`.
- `format`: placeholders `{title}`, `{summary}`, `{special}`, `{time}`. Lines containing only `{special}` are dropped when no special instruction is given.
- Add another agent by creating a ClawBot login in its own directory and adding an entry here.

## Submission Format (daily-summary)

```
【标题】
简要说明完成了什么（≤200字）
我的特别指示：...        ← 可选
「2026-10-19 15:04」
```

## Requirements

- The target ClawBot must have a recent `context.json`; if missing, the user must first send any message to that agent in WeChat.
- `clawbot.py` handles login and sending.
- Reports are plain text; WeChat mobile renders newlines, desktop collapses them.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Agent not found | Add an entry to `config.json` with its `clawbot_dir` |
| Summary over the limit | Shorten it; the script truncates and warns |
| `context_token` missing | Ask the user to send one message to that agent first |
| Reporting to a person | Use WeChat directly; this skill is only for configured agents |

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
python -m pip install requests cryptography
# then edit %USERPROFILE%\.claude\wechat-agent-report\config.json
```
