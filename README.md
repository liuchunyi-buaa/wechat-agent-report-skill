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
python -m pip install winsdk pillow
```

需要 Windows 微信客户端（4.x）和 Python 3。OCR 依赖 `winsdk`（Windows 自带 OCR）和 `pillow`；还需安装中文（简体）OCR 语言包。`install.ps1` 只负责复制文件，发送逻辑在 `send_report.py` 中运行，不需要 PowerShell。

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

占位符：`{title}`、`{summary}`、`{special}`、`{time}`、`{device}`。只有 `{special}` 的那一行在未提供特别说明时会自动删除；`{device}` 自动填当前电脑的主机名。

`references/daily-summary.md`：

```
【{title}】
{summary}
<特别说明>{special}
「{time}」
「{device}」
```

新增 agent：

1. 在 `references/` 新建 `<agent>.md`，写入该 agent 的提交格式。
2. 在 `config.json` 的 `agents` 里加一条，指定 `wechat_name` 和 `reference`。

## 使用

Windows 使用 `python`，macOS / Linux 使用 `python3`。

```bash
# 查看已配置的 agent
python ~/.claude/skills/wechat-agent-report/scripts/send_report.py --list

# 发送
python ~/.claude/skills/wechat-agent-report/scripts/send_report.py \
  --agent daily-summary \
  --title "完成登录页重构" \
  --summary "重构了表单校验和错误提示，补充 6 个单元测试，已合并。" \
  --special "下次优先处理移动端适配"

# 只定位对话并填入消息，不按回车（验证用）
python ~/.claude/skills/wechat-agent-report/scripts/send_report.py \
  --agent daily-summary --title "测试" --summary "测试内容" --dry-run
```

`--special` 可省略，时间自动填当前时间。

## 发送原理

1. 按模板生成消息
2. 激活微信并搜索 `wechat_name`
3. 对搜索区域截图并 OCR，点击包含“微信 ClawBot”的对话行
4. Windows 额外校验已打开对话的标题，然后粘贴消息并回车

macOS 使用 AppleScript + Vision OCR（`find_and_click.swift`）；Windows 在 `send_report.py` 中使用 Windows OCR + Pillow，流程与 macOS 一致，不使用 PowerShell。发送时会短暂占用键盘焦点，请勿同时操作键鼠。

## 为什么不用 ClawBot API

ClawBot 的出站消息不会回到 `getupdates`。通过 API 发送（BOT 消息）时，每日总结读不到；通过微信界面以用户身份发送，ClawBot 才能收到并纳入总结。

## 常见问题

| 现象 | 处理 |
|------|------|
| 打开了错误的对话 | `wechat_name` 必须与微信搜索显示完全一致 |
| 消息发到别的窗口 | 脚本会激活微信，运行期间不要抢焦点 |
| Windows 报“缺少依赖” | 运行 `python -m pip install winsdk pillow` |
| Windows 报“在搜索结果中找不到对话” | 确认微信窗口未被缩放或拖动，且已安装中文 OCR 语言包 |
| 想先验证但不发送 | 加 `--dry-run` |
| 摘要被截断 | 缩短摘要或调大 `max_words` |
| 没有特别说明 | 正常，模板中那一行会自动省略 |

## 目录

```
wechat-agent-report-skill/
├── SKILL.md
├── README.md
├── install.sh
├── install.ps1
├── config.example.json
├── references/
│   └── daily-summary.md
└── scripts/
    ├── send_report.py
    ├── send_ui_macos.sh
    └── find_and_click.swift
```
