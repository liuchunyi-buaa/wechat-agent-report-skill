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

```bat
git clone https://github.com/liuchunyi-buaa/wechat-agent-report-skill.git
cd wechat-agent-report-skill
install.bat
python -m pip install winsdk pillow
```

需要 Windows 微信客户端（4.x）和 Python 3。OCR 依赖 `winsdk`（Windows 自带 OCR）和 `pillow`；还需安装中文（简体）OCR 语言包。`install.bat` 只负责复制文件，发送逻辑在 `send_report.py` 中运行，不使用 PowerShell。

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
- `max_words`：背景 + 摘要的字数上限；超出时脚本拒绝发送，不会截断
- `reference`：提交模板，相对于配置目录

## 提交模板

模板放在 `~/.claude/wechat-agent-report/references/`，每个 agent 一个文件。

占位符：`{project}`、`{title}`、`{background}`、`{summary}`、`{special}`、`{time}`、`{device}`。只有 `{special}` 的那一行在未提供特别说明时会自动删除；`{device}` 自动填当前电脑的主机名。模板必须包含 `{project}` 与 `{background}`，否则脚本报错拒绝发送，避免报告丢失项目背景。

`references/daily-summary.md`：

```
【{project}｜{title}】
背景：{background}
{summary}
<特别说明>{special}
「{time}」
「{device}」
```

新增 agent：

1. 在 `references/` 新建 `<agent>.md`，写入该 agent 的提交格式。
2. 在 `config.json` 的 `agents` 里加一条，指定 `wechat_name` 和 `reference`。

## 报告内容要求

接收方只看得到这一条消息，因此每条报告都必须自包含：

- **项目名**：标题里带项目名，如 `【SMALL SILENT HUMAN｜前端改造完成】`
- **项目背景**：一句话说清项目是什么、技术栈/仓库、要解决的问题
- **本次任务**：只写这一次做了什么，不要把整个项目的进展混进来
- **验证与遗留**：测了什么、通过多少；还有什么没做

不要依赖“上一条”“以此条为准”来补充信息。内容超长时先压缩再发送，不要先发残缺版本。

## 使用

Windows 使用 `python`，macOS / Linux 使用 `python3`。

```bash
# 查看已配置的 agent
python ~/.claude/skills/wechat-agent-report/scripts/send_report.py --list

# 先预检：只生成消息并显示字数，不碰微信
python ~/.claude/skills/wechat-agent-report/scripts/send_report.py \
  --agent daily-summary \
  --project "SMALL SILENT HUMAN" \
  --title "前端改造完成" \
  --background "鸿蒙 ArkTS 应用的崩溃日志→定位→修复→真机回归链路（仓库 small_silent_human）" \
  --summary "web/ 四视图与五级日志完成，前端测试 40 项通过。" \
  --check

# 发送
python ~/.claude/skills/wechat-agent-report/scripts/send_report.py \
  --agent daily-summary \
  --project "SMALL SILENT HUMAN" \
  --title "前端改造完成：demo 草稿落成可交付 web/" \
  --background "北航-华为可靠性创新实验室挑战赛 B 题，鸿蒙 ArkTS 应用的崩溃日志→定位→修复→真机回归链路（仓库 small_silent_human）" \
  --summary "把 10-16 demo 草稿落成 web/：单端口 Python 服务 + 四个视图，start.bat [9] 启动；实时项目清单、运行页三栏+五级日志、报告页根因定位、调用图风险地图。前端测试 40 项通过。" \
  --special "模拟器卡住，真机回归待恢复后复跑"

# 只定位对话并填入消息，不按回车（验证用）
python ~/.claude/skills/wechat-agent-report/scripts/send_report.py \
  --agent daily-summary --project "测试项目" --title "测试" \
  --background "用于验证发送链路的合成项目。" --summary "测试内容" --dry-run
```

`--project`、`--title`、`--background`、`--summary` 必填。`--special` 可省略，时间自动填当前时间。背景 + 摘要超过 `max_words` 时脚本报错并拒绝发送，不会截断。

## 发送原理

1. 按模板生成消息
2. 激活微信并搜索 `wechat_name`
3. 对搜索区域截图并 OCR，点击包含“微信 ClawBot”的对话行
4. Windows 额外校验已打开对话的标题，然后粘贴消息并回车

macOS 使用 AppleScript + Vision OCR（`find_and_click.swift`）；Windows 在 `send_report.py` 中使用 Windows OCR + Pillow，流程与 macOS 一致，不使用 PowerShell。发送时会短暂占用键盘焦点，请勿同时操作键鼠。

脚本不会启动微信：已登录的微信在后台或托盘时会被激活/还原主窗口；如果微信没有运行，脚本直接报错退出，请手动启动并登录。重复启动已登录的客户端会掉到登录页。

## 为什么不用 ClawBot API

ClawBot 的出站消息不会回到 `getupdates`。通过 API 发送（BOT 消息）时，每日总结读不到；通过微信界面以用户身份发送，ClawBot 才能收到并纳入总结。

## 常见问题

| 现象 | 处理 |
|------|------|
| 每日总结说“不知道是哪件事” | 报告缺项目名或背景；用 `--project`、`--background` 补全，摘要不要写“如上/上一条” |
| 提示“内容超长”并拒绝发送 | 背景 + 摘要超过 `max_words`；压缩摘要后重试，或与用户确认后调大 `max_words` |
| 想先看完整消息和字数 | 加 `--check`，只打印不发送 |
| 提示“主窗口在后台或托盘里” | 点击托盘/任务栏的微信图标打开主窗口后重试；不要重启微信 |
| 微信停在登录页 | 先手动登录；脚本不会启动微信，重复启动已登录的客户端会导致掉登录 |
| 打开了错误的对话 | `wechat_name` 必须与微信搜索显示完全一致 |
| 消息发到别的窗口 | 脚本会激活微信，运行期间不要抢焦点 |
| Windows 报“缺少依赖” | 运行 `python -m pip install winsdk pillow` |
| 报“在搜索结果中找不到对话” | 确认微信窗口未被缩放或拖动、已安装中文 OCR 语言包，且微信已登录（不要在登录页时重启客户端） |
| 想先验证但不发送 | 加 `--dry-run`（会操作微信）；纯预检用 `--check` |
| 没有特别说明 | 正常，模板中那一行会自动省略 |

## 目录

```
wechat-agent-report-skill/
├── SKILL.md
├── README.md
├── install.sh
├── install.bat
├── install.ps1        # 旧版 PowerShell 安装，保留但不再使用
├── config.example.json
├── references/
│   └── daily-summary.md
└── scripts/
    ├── send_report.py
    ├── send_ui_macos.sh
    └── find_and_click.swift
```
