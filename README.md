# WeChat Agent Report Skill

通过操控微信桌面界面，向配置好的微信 agent 对话发送任务完成报告。消息以用户本人身份发出，目标 agent 能收到并纳入后续总结。

支持 macOS 和 Windows，支持任意多个 agent 对话，每个 agent 有自己的提交模板。

## 安装

### macOS

```bash
git clone https://github.com/liuchunyi-buaa/wechat-agent-report-skill.git
cd wechat-agent-report-skill
bash install.sh
```

需要在「系统设置 → 隐私与安全性 → 辅助功能」中允许终端或 Claude。

### Windows

```powershell
git clone https://github.com/liuchunyi-buaa/wechat-agent-report-skill.git
cd wechat-agent-report-skill
powershell -ExecutionPolicy Bypass -File install.ps1
```

需要 Windows 微信客户端和 PowerShell 5+。

## 配置

编辑 `~/.claude/wechat-agent-report/config.json`（Windows 为 `%USERPROFILE%\.claude\wechat-agent-report\config.json`）：

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

- `wechat_name`：微信搜索里显示的完整对话名
- `max_words`：摘要字数上限
- `reference`：提交模板，相对于配置目录

## 提交模板

模板放在 `~/.claude/wechat-agent-report/references/`，每个 agent 一个文件。

占位符：`{title}`、`{summary}`、`{special}`、`{time}`。只有 `{special}` 的那一行在未提供特别说明时会自动删除。

`references/daily-summary.md`：

```
【{title}】
{summary}
<特别说明>{special}
「{time}」
```

新增 agent：

1. 在 `references/` 新建 `<agent>.md`，写入该 agent 的提交格式。
2. 在 `config.json` 的 `agents` 里加一条，指定 `wechat_name` 和 `reference`。

## 使用

```bash
# 查看已配置的 agent
python3 ~/.claude/skills/wechat-agent-report/scripts/send_report.py --list

# 发送
python3 ~/.claude/skills/wechat-agent-report/scripts/send_report.py \
  --agent daily-summary \
  --title "完成登录页重构" \
  --summary "重构了表单校验和错误提示，补充 6 个单元测试，已合并。" \
  --special "下次优先处理移动端适配"
```

`--special` 可省略，时间自动填当前时间。

## 发送原理

1. 按模板生成消息
2. 激活微信，搜索并打开 `wechat_name`
3. 粘贴消息并回车

macOS 用 AppleScript，Windows 用 PowerShell SendKeys。发送时会短暂占用键盘焦点，请勿同时操作键鼠。

## 为什么不用 ClawBot API

ClawBot 的出站消息不会回到 `getupdates`。通过 API 发送（BOT 消息）时，每日总结读不到；通过微信界面以用户身份发送，ClawBot 才能收到并纳入总结。

## 常见问题

| 现象 | 处理 |
|------|------|
| 打开了错误的对话 | `wechat_name` 必须与微信搜索显示完全一致 |
| 消息发到别的窗口 | 脚本会激活微信，运行期间不要抢焦点 |
| 摘要被截断 | 缩短摘要或调大 `max_words` |
| 没有特别说明 | 正常，模板中那一行会自动省略 |

## 目录

```
wechat-agent-report-skill/
├── SKILL.md
├── install.sh
├── install.ps1
├── config.example.json
├── references/
│   └── daily-summary.md
└── scripts/
    ├── send_report.py
    ├── send_ui_macos.sh
    └── send_ui_windows.ps1
```
