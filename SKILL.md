---
name: wechat-agent-report
description: Use when sending a task completion report, status update, or daily summary to a configured WeChat agent conversation (such as 每日总结 Agent), or when the user asks to 发给每日总结 / 汇报 / 通知 / 同步给微信 agent.
---

# WeChat Agent Report

## 概述

通过驱动微信桌面界面，把格式化报告以用户本人身份发到指定 agent 对话。消息发出后，接收方只能看到这一条——它看不到你的会话、仓库和上下文。

**核心原则：报告必须自带项目身份和背景，单独看就能知道「这是哪个项目、这次做了什么」。**

## 何时使用

- 用户要求通知某个微信 agent 任务已完成
- 你完成的工作需要被每日总结等 agent 记录
- 用户说「发给每日总结」「汇报一下」「同步给微信 agent」

不要用于普通联系人或群聊。

## 发送前必须澄清的四项

拼报告之前，先从当前会话、当前目录（仓库名 / git remote）、用户的话里确定下面四项。确定不了就问用户，不要猜，也不要省略：

| 项目 | 要求 |
|---|---|
| 项目名 | 用于标题，如 `SMALL SILENT HUMAN`；有仓库名一并写进背景 |
| 项目背景 | 一句话说清「这是什么项目」：比赛/产品/业务、技术栈、要解决的问题。写给完全没看过这个项目的人；不能只重复项目名 |
| 本次任务 | 这一次具体做了什么，不要写成整个项目的进展 |
| 验证与遗留 | 测了什么、通过多少；还有什么没做、卡在哪里 |

第一条消息就必须包含这些信息。不要等接收方反问「不知道你说的是哪件事」再补。

## 消息结构

模板（`references/daily-summary.md`）：

```
【{project}｜{title}】
背景：{background}
{summary}
<特别说明>{special}
「{time}」
「{device}」
```

- `{project}`：项目名（必填）
- `{title}`：本次做了什么（必填）
- `{background}`：项目背景（必填）
- `{summary}`：本次改动与验证结果（必填）
- `{special}`：遗留风险、未完成项（可选）
- `{time}`、`{device}`：脚本自动填

反例 → 正例：

- 标题 `【前端改造完成】` → `【SMALL SILENT HUMAN｜前端改造完成：demo 草稿落成可交付 web/】`
- 没有背景 → `背景：北航-华为可靠性创新实验室挑战赛 B 题，鸿蒙 ArkTS 应用的崩溃日志→定位→修复→真机回归链路（仓库 small_silent_human）`
- 摘要写「如上」「接着上次」 → 每次自成一体，接收方没有上文

## 发送流程（按顺序执行）

1. 按上表整理四项信息；缺项目名或背景时先问用户。
2. 写 `--background`：一句话，包含项目定位 + 技术栈/仓库。
3. 写 `--summary`：本次改动（按模块列关键点）+ 验证结果（测试数、真机/模拟器状态）。
4. **先运行 `--check`**，检查完整消息的字数和可读性。
5. 超长就压缩摘要（保留项目背景和验证结论，删实现细节），再次 `--check`。
6. 通过后正式发送。**一次发一条完整消息，不要先发残缺再补发。**

`--check` 之后逐条确认：

- 标题里有项目名
- 背景读完能回答「这是什么项目、解决什么问题」，不是只重复项目名
- 摘要有「本次做了什么 + 验证结果」
- 没有「如上」「上一条」「以此条为准」等依赖上文的说法
- 背景 + 摘要在 `max_words` 内
- 整条消息单独看能看懂

```bash
python ~/.claude/skills/wechat-agent-report/scripts/send_report.py --list

# 1. 先预检：只生成消息并显示字数，不碰微信
python ~/.claude/skills/wechat-agent-report/scripts/send_report.py \
  --agent daily-summary \
  --project "SMALL SILENT HUMAN" \
  --title "前端改造完成：demo 草稿落成可交付 web/" \
  --background "北航-华为可靠性创新实验室挑战赛 B 题，鸿蒙 ArkTS 应用的崩溃日志→定位→修复→真机回归链路（仓库 small_silent_human）" \
  --summary "把 10-16 demo 草稿落成 web/：单端口 Python 服务 + 四个视图，start.bat [9] 启动；实时项目清单（27 条/22 条可跑）、运行页三栏+五级日志、报告页根因定位、调用图风险地图。前端测试 40 项通过。" \
  --special "模拟器卡住，真机回归待恢复后复跑；3 个配图脚本仍未跟踪" \
  --check

# 2. 确认无误后去掉 --check 再执行，正式发送
```

- `--special` 可省略。
- 时间自动填 `「YYYY-MM-DD HH:MM」`。

## 字数上限

- `max_words`（默认 200）限制 **背景 + 摘要** 的总字数。
- 超出时脚本报错并**拒绝发送**，不会截断。
- 压缩顺序：先删实现细节和修饰语，再压缩验证描述；**最后才动项目背景**，背景不能删到看不懂。
- 确实需要放宽时，改配置里的 `max_words`，并先和用户确认接收方能否接受。

## 配置

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

- `wechat_name`：微信搜索里显示的完整对话名。
- `max_words`：背景 + 摘要的字数上限。
- `reference`：提交模板，相对配置文件所在目录。
- 新增 agent：在 `references/` 新建 `<agent>.md`，再在 `agents` 里加一条。

## Agent 模板

模板放在 `~/.claude/wechat-agent-report/references/`。占位符：`{project}`、`{title}`、`{background}`、`{summary}`、`{special}`、`{time}`、`{device}`。

- 只有 `{special}` 的那一行在未提供特别说明时自动删除。
- 模板必须包含 `{project}` 和 `{background}`，否则脚本报错拒绝发送——这是防止报告丢失项目背景的结构性保证。
- `{device}` 是当前电脑的主机名。

## 发送原理

1. 按模板生成消息。
2. 激活微信，搜索 `wechat_name`，对结果区截图并 OCR。
3. 点击包含「微信 ClawBot」的对话行（真实对话，不是搜索建议）；Windows 会先校验已打开对话的标题。
4. 粘贴消息并回车。

macOS 使用 AppleScript + Vision OCR（`find_and_click.swift`）；Windows 在 `send_report.py` 内使用 Windows OCR + Pillow，运行时不经过 PowerShell。两端发送时都会短暂占用键盘焦点。

`--check` 只生成并打印消息，不启动微信；`--dry-run` 会定位对话并填入消息，但不按回车。

## 不要启动微信

脚本只负责定位窗口、搜索对话和发送，**不会也不应该启动微信**。看到「主窗口在后台或托盘里」时：

1. 让用户点击托盘/任务栏的微信图标打开主窗口；
2. 等用户确认后再重试；
3. 不要执行 `start Weixin.exe`、`open -a WeChat`、`Start-Process Weixin` 或任何等价命令——重复启动已登录的客户端会掉到登录页。

## 依赖

- 微信桌面客户端已登录，且主窗口存在（在后台或托盘里都可以，脚本会把它拉到前台）
- macOS：给终端 / Claude 开启「辅助功能」权限
- Windows：Python 3、`pip install winsdk pillow`、中文 OCR 语言包、微信 4.x 客户端
- 脚本运行期间不要输入、点击或缩放微信窗口

## 常见错误

| 现象 | 原因 | 处理 |
|---|---|---|
| 每日总结说「不知道是哪件事」 | 标题/摘要没写项目名和背景 | 必填 `--project`、`--background` |
| 消息被截断 | 想靠脚本截断 | 先 `--check`；超长就压缩后重发 |
| 连发多条「以此条为准」 | 第一条缺背景，补发又超长 | 发送前自检，一条到位；确实发错只补发一条完整版 |
| 摘要出现「如上」「上一条」 | 依赖接收方看不到的上下文 | 每次报告自包含 |
| 提示「主窗口在后台或托盘里」 | 微信已运行，但窗口被隐藏 | 点击托盘/任务栏的微信图标打开主窗口后重试；**不要重启微信** |
| 微信停在登录页 | 重复启动了已登录的客户端 | 先手动登录；脚本不会启动或登录微信 |
| 打开了错误的对话 | `wechat_name` 与微信搜索不一致 | 用微信搜索里显示的完整名称 |
| 消息发到别的窗口 | 运行期间抢了焦点 | 脚本会激活微信，期间不要操作键鼠 |
| Windows 报「缺少依赖」 | 未安装 OCR 依赖 | `python -m pip install winsdk pillow` |
| 报「在搜索结果中找不到对话」 | 窗口被缩放/拖动、缺中文 OCR 语言包，或微信停在登录页 | 保持窗口不变、安装中文语言包；若在登录页先登录，不要重启微信 |
| 没有特别说明 | 正常 | 该行会自动省略 |

## 部署

macOS / Linux：

```bash
git clone https://github.com/liuchunyi-buaa/wechat-agent-report-skill.git
cd wechat-agent-report-skill
bash install.sh
# 然后编辑 ~/.claude/wechat-agent-report/config.json
```

Windows（cmd）：

```bat
git clone https://github.com/liuchunyi-buaa/wechat-agent-report-skill.git
cd wechat-agent-report-skill
install.bat
python -m pip install winsdk pillow
# 然后编辑 %USERPROFILE%\.claude\wechat-agent-report\config.json
```

`install.bat` 只复制文件；发送逻辑本身在 Python 中运行，不使用 PowerShell。旧的 `install.ps1` 仍保留，但不再使用。
