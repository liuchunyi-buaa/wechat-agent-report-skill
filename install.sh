#!/bin/bash
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
SKILL_DEST="$HOME/.claude/skills/wechat-agent-report"
CONFIG_DIR="$HOME/.claude/wechat-agent-report"

mkdir -p "$SKILL_DEST/scripts" "$CONFIG_DIR/references"
cp "$SRC/SKILL.md" "$SKILL_DEST/SKILL.md"
cp "$SRC/scripts/send_report.py" "$SKILL_DEST/scripts/"
cp "$SRC/scripts/send_ui_macos.sh" "$SKILL_DEST/scripts/"
cp "$SRC/scripts/find_and_click.swift" "$SKILL_DEST/scripts/"
cp "$SRC/references/"* "$CONFIG_DIR/references/"
chmod +x "$SKILL_DEST/scripts/send_report.py" "$SKILL_DEST/scripts/send_ui_macos.sh"
if command -v swiftc >/dev/null 2>&1; then
    swiftc -O "$SKILL_DEST/scripts/find_and_click.swift" -o "$SKILL_DEST/scripts/find_and_click" 2>/dev/null || true
fi

if [ ! -f "$CONFIG_DIR/config.json" ]; then
    cp "$SRC/config.example.json" "$CONFIG_DIR/config.json"
    echo "已创建配置：$CONFIG_DIR/config.json"
else
    echo "配置已存在，未覆盖：$CONFIG_DIR/config.json"
fi

echo "安装完成。"
echo "1. 编辑 $CONFIG_DIR/config.json，填写 wechat_name（微信里显示的对话名）"
echo "2. macOS 需在「系统设置 → 隐私与安全性 → 辅助功能」中允许终端/Claude"
echo "3. 运行：python3 $SKILL_DEST/scripts/send_report.py --list"
echo "4. 预检：python3 $SKILL_DEST/scripts/send_report.py --agent daily-summary --project \"项目名\" --title \"标题\" --background \"项目背景\" --summary \"完成内容\" --check"
echo "5. 发送：去掉 --check 再执行一次"
