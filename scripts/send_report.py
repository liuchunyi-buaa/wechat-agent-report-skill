#!/usr/bin/env python3
import argparse
import datetime
import json
import os
import subprocess
import sys
import tempfile

DEFAULT_CONFIG = os.path.expanduser("~/.claude/wechat-agent-report/config.json")
DEFAULT_FORMAT = "【{title}】\n{summary}\n{special}\n「{time}」"


def load_config(path):
    if not os.path.exists(path):
        sys.exit("配置文件不存在：%s\n请先运行 install.sh 或手动创建。" % path)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def truncate(text, limit):
    if len(text) <= limit:
        return text, False
    return text[: max(0, limit - 1)] + "…", True


def build_message(fmt, title, summary, special, now):
    lines = []
    for line in fmt.split("\n"):
        if "{special}" in line and not special:
            continue
        lines.append(
            line.replace("{title}", title)
            .replace("{summary}", summary)
            .replace("{special}", special or "")
            .replace("{time}", now)
        )
    return "\n".join(lines)


def cmd_list(config):
    agents = config.get("agents", {})
    if not agents:
        print("没有配置任何 agent")
        return
    for name, cfg in agents.items():
        print("%s\t%s" % (name, cfg.get("clawbot_dir", "")))


def main():
    parser = argparse.ArgumentParser(description="向配置好的微信 agent 对话发送任务完成报告")
    parser.add_argument("--config", default=os.environ.get("WECHAT_AGENT_REPORT_CONFIG", DEFAULT_CONFIG))
    parser.add_argument("--list", action="store_true", help="列出已配置的 agent")
    parser.add_argument("--agent", help="agent 名称")
    parser.add_argument("--title", help="报告标题")
    parser.add_argument("--summary", help="完成内容摘要")
    parser.add_argument("--file", help="从文件读取摘要")
    parser.add_argument("--special", default="", help="特别指示（可选）")
    parser.add_argument("--time", default=None, help="时间，默认当前时间")
    args = parser.parse_args()

    config = load_config(args.config)
    if args.list:
        cmd_list(config)
        return 0

    if not args.agent or not args.title:
        sys.exit("需要 --agent 和 --title")

    agents = config.get("agents", {})
    if args.agent not in agents:
        sys.exit("未配置 agent：%s（可用：%s）" % (args.agent, ", ".join(agents) or "无"))
    cfg = agents[args.agent]

    if args.file:
        with open(args.file, encoding="utf-8") as f:
            summary = f.read().strip()
    elif args.summary:
        summary = args.summary.strip()
    else:
        sys.exit("需要 --summary 或 --file")
    if not summary:
        sys.exit("summary 为空")

    limit = int(cfg.get("max_words", 200))
    summary, truncated = truncate(summary, limit)
    if truncated:
        print("警告：摘要超过 %d 字，已截断" % limit, file=sys.stderr)

    now = args.time or datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    message = build_message(
        cfg.get("format", DEFAULT_FORMAT),
        args.title.strip(),
        summary,
        args.special.strip(),
        now,
    )

    clawbot_dir = os.path.expanduser(cfg.get("clawbot_dir", ""))
    clawbot = os.path.join(clawbot_dir, "clawbot.py")
    context = os.path.join(clawbot_dir, "context.json")
    if not os.path.exists(clawbot):
        sys.exit("找不到 clawbot.py：%s" % clawbot)
    if not os.path.exists(context):
        sys.exit("缺少 context.json：%s\n请先在微信里给该 agent 发一条消息。" % context)

    fd, tmp = tempfile.mkstemp(prefix="wechat-report-", suffix=".txt")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(message)
        result = subprocess.run([sys.executable, clawbot, "send", "--file", tmp])
        if result.returncode != 0:
            sys.exit("发送失败，退出码 %d" % result.returncode)
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass

    print("已发送给 %s：%s" % (args.agent, args.title))
    return 0


if __name__ == "__main__":
    sys.exit(main())
