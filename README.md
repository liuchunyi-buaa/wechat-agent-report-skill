# WeChat Agent Report Skill

通过 ClawBot API 向配置好的微信 agent 对话发送任务完成报告。支持多个 agent，每个 agent 可以有自己的提交格式和 ClawBot 凭证。

## 安装

```bash
git clone https://github.com/liuchunyi-buaa/wechat-agent-report-skill.git
cd wechat-agent-report-skill
bash install.sh
```

安装后：

- Skill 位于 `~/.claude/skills/wechat-agent-report/`
- 配置位于 `~/.claude/wechat-agent-report/config.json`

## 配置

编辑 `~/.claude/wechat-agent-report/config.json`：

```json
{
  "agents": {
    "daily-summary": {
      "clawbot_dir": "/path/to/clawbot",
      "max_words": 200,
      "format": "【{title}】\n{summary}\n{special}\n「{time}」"
    }
  }
}
```

- `clawbot_dir`：包含 `clawbot.py`、`credentials.json`、`context.json` 的目录
- `max_words`：摘要字数上限，默认 200
- `format`：消息模板，支持 `{title}`、`{summary}`、`{special}`、`{time}`
- 换一个 agent 对话，只需新增一个条目，并让它指向另一个已登录的 ClawBot 目录

## 使用

```bash
# 查看已配置的 agent
python3 ~/.claude/skills/wechat-agent-report/scripts/send_report.py --list

# 发送报告
python3 ~/.claude/skills/wechat-agent-report/scripts/send_report.py \
  --agent daily-summary \
  --title "完成登录页重构" \
  --summary "重构了表单校验和错误提示，补充 6 个单元测试，已合并。" \
  --special "下次优先处理移动端适配"
```

`--special` 可省略。时间自动填当前时间。

## 提交格式

daily-summary 的格式：

```
【标题】
简要说明完成了什么（≤200字）
我的特别指示：...（可选）
「2026-10-19 15:04」
```

其他 agent 在配置中用 `format` 定义各自的格式。

## 前提与限制

- 目标 ClawBot 必须有最近的 `context.json`；没有时，先在手机微信给该 agent 发一条消息
- 发送通过 ClawBot 官方接口，不操控微信界面
- 微信手机端正常换行，桌面端会把换行折叠成空格
- 凭证和配置只保存在本机，不要提交到仓库

## 目录

```
wechat-agent-report-skill/
├── SKILL.md
├── install.sh
├── config.example.json
└── scripts/send_report.py
```
