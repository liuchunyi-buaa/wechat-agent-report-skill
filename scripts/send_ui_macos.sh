#!/bin/bash
set -euo pipefail

NAME_FILE="${WECHAT_AGENT_NAME_FILE:?缺少 WECHAT_AGENT_NAME_FILE}"
MSG_FILE="${WECHAT_AGENT_MESSAGE_FILE:?缺少 WECHAT_AGENT_MESSAGE_FILE}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FINDER="$SCRIPT_DIR/find_and_click"
if [ ! -x "$FINDER" ]; then
    FINDER="$SCRIPT_DIR/find_and_click.swift"
fi

run_finder() {
    if [ -x "$FINDER" ]; then
        "$FINDER" "$@"
    else
        swift "$FINDER" "$@"
    fi
}

open -a /Applications/WeChat.app
sleep 1
osascript -e 'tell application "System Events" to tell process "WeChat"
    set frontmost to true
    try
        perform action "AXRaise" of window "微信"
    end try
end tell' >/dev/null 2>&1 || true
sleep 0.6

INFO=$(osascript -e 'tell application "System Events" to tell process "WeChat"
    set bestInfo to missing value
    repeat with w in windows
        try
            set ws to size of w
            set ww to item 1 of ws
            set wh to item 2 of ws
            if ww > 600 and ww < 1200 and wh > 400 and wh < 900 then
                set bestInfo to {position of w, size of w}
                exit repeat
            end if
        end try
    end repeat
    return bestInfo
end tell' 2>/dev/null || true)
WX=$(printf '%s' "$INFO" | cut -d, -f1 | tr -d ' ')
WY=$(printf '%s' "$INFO" | cut -d, -f2 | tr -d ' ')
WW=$(printf '%s' "$INFO" | cut -d, -f3 | tr -d ' ')
WH=$(printf '%s' "$INFO" | cut -d, -f4 | tr -d ' ')

# 回到聊天主界面：点击左侧聊天图标
if [ -n "${WX:-}" ] && [ -n "${WY:-}" ] && [ -n "${WW:-}" ] && [ -n "${WH:-}" ]; then
    run_finder --point $((WX + WW * 7 / 100)) $((WY + WH * 23 / 100)) >/dev/null 2>&1 || true
    sleep 0.8
fi

CLIP_TMP=$(mktemp)
pbpaste > "$CLIP_TMP" 2>/dev/null || true
restore() {
    osascript -e "set the clipboard to (read POSIX file \"$CLIP_TMP\" as «class utf8»)" 2>/dev/null || true
    rm -f "$CLIP_TMP"
}
trap restore EXIT

# 搜索目标对话
osascript -e "set the clipboard to (read POSIX file \"$NAME_FILE\" as «class utf8»)"
osascript -e 'tell application "System Events" to keystroke "f" using command down'
sleep 0.8
osascript -e 'tell application "System Events" to keystroke "a" using command down'
osascript -e 'tell application "System Events" to keystroke "v" using command down'
sleep 1.6

# OCR 定位搜索结果中的 ClawBot 对话并点击
SHOT="$(mktemp -t wxsearch).png"
CLICKED=0
if [ -n "${WX:-}" ] && [ -n "${WY:-}" ] && [ -n "${WW:-}" ] && [ -n "${WH:-}" ]; then
    screencapture -x -R"$WX,$WY,$WW,$WH" "$SHOT" 2>/dev/null || true
    if run_finder "$SHOT" "微信 ClawBot" "$WX" "$WY" "$WW" "$WH" >/dev/null 2>&1; then
        CLICKED=1
    elif run_finder "$SHOT" "ClawBot" "$WX" "$WY" "$WW" "$WH" >/dev/null 2>&1; then
        CLICKED=1
    fi
fi
rm -f "$SHOT"

if [ "$CLICKED" -eq 0 ]; then
    echo "未能定位微信对话，请确认对话名与微信搜索显示一致" >&2
    exit 3
fi
sleep 1.3

# 粘贴并发送
osascript -e "set the clipboard to (read POSIX file \"$MSG_FILE\" as «class utf8»)"
sleep 0.2
osascript -e 'tell application "System Events" to keystroke "v" using command down'
sleep 0.6
osascript -e 'tell application "System Events" to key code 36'
sleep 0.8
