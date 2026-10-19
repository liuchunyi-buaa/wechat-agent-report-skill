#!/bin/bash
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
SKILL_DEST="$HOME/.claude/skills/wechat-agent-report"
CONFIG_DIR="$HOME/.claude/wechat-agent-report"

mkdir -p "$SKILL_DEST/scripts" "$CONFIG_DIR"
cp "$SRC/SKILL.md" "$SKILL_DEST/SKILL.md"
cp "$SRC/scripts/send_report.py" "$SKILL_DEST/scripts/send_report.py"
chmod +x "$SKILL_DEST/scripts/send_report.py"

if [ ! -f "$CONFIG_DIR/config.json" ]; then
    cp "$SRC/config.example.json" "$CONFIG_DIR/config.json"
    echo "已创建配置：$CONFIG_DIR/config.json"
else
    echo "配置已存在，未覆盖：$CONFIG_DIR/config.json"
fi

echo "安装完成。"
echo "1. 编辑 $CONFIG_DIR/config.json，把 clawbot_dir 指向你的 ClawBot 目录"
echo "2. 运行：python3 $SKILL_DEST/scripts/send_report.py --list"
echo "3. 发送：python3 $SKILL_DEST/scripts/send_report.py --agent daily-summary --title \"标题\" --summary \"完成内容\""
