#!/usr/bin/env python3
"""Send a formatted report to a configured WeChat agent conversation.

Windows mirrors the macOS implementation:
  1. bring WeChat to the front
  2. focus search, clear it, paste the conversation name
  3. screenshot the WeChat window region, OCR it, click the row that
     contains "微信 ClawBot" (the real conversation, not a suggestion)
  4. paste the report and press Enter

Windows extras: the opened chat title is verified by OCR before sending,
and --dry-run stops right before the final Enter.
"""

import argparse
import asyncio
import datetime
import difflib
import json
import os
import socket
import subprocess
import sys
import tempfile

DEFAULT_CONFIG = os.path.expanduser("~/.claude/wechat-agent-report/config.json")
DEFAULT_FORMAT = (
    "【{project}｜{title}】\n"
    "背景：{background}\n"
    "{summary}\n"
    "<特别说明>{special}\n"
    "「{time}」"
)
REQUIRED_PLACEHOLDERS = ("{project}", "{title}", "{background}", "{summary}")


# ---------------------------------------------------------------------------
# Windows implementation
# ---------------------------------------------------------------------------
if sys.platform.startswith("win"):
    import ctypes
    import time
    from ctypes import wintypes as _wt

    try:
        from PIL import ImageGrab
    except ImportError:
        ImageGrab = None

    try:
        from winsdk.windows.media.ocr import OcrEngine as _OcrEngine
        from winsdk.windows.globalization import Language as _Language
        from winsdk.windows.storage import (
            StorageFile as _StorageFile,
            FileAccessMode as _FileAccessMode,
        )
        from winsdk.windows.graphics.imaging import BitmapDecoder as _BitmapDecoder
    except ImportError:
        _OcrEngine = None

    _user32 = ctypes.windll.user32
    _kernel32 = ctypes.windll.kernel32

    _CF_UNICODETEXT = 13
    _GMEM_MOVEABLE = 0x0002
    _VK_CONTROL = 0x11
    _VK_A = 0x41
    _VK_V = 0x56
    _VK_BACK = 0x08
    _VK_RETURN = 0x0D
    _VK_ALT = 0x12

    _EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, _wt.HWND, _wt.LPARAM)

    # ctypes defaults to 32-bit ints; handles and pointers would be truncated.
    _user32.OpenClipboard.argtypes = [ctypes.c_void_p]
    _user32.OpenClipboard.restype = ctypes.c_bool
    _user32.CloseClipboard.restype = ctypes.c_bool
    _user32.EmptyClipboard.restype = ctypes.c_bool
    _user32.GetClipboardData.argtypes = [ctypes.c_uint]
    _user32.GetClipboardData.restype = ctypes.c_void_p
    _user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
    _user32.SetClipboardData.restype = ctypes.c_void_p
    _user32.GetForegroundWindow.restype = ctypes.c_void_p
    _user32.SetForegroundWindow.argtypes = [ctypes.c_void_p]
    _user32.SetForegroundWindow.restype = ctypes.c_bool
    _user32.ShowWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]
    _user32.ShowWindow.restype = ctypes.c_bool
    _user32.AttachThreadInput.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.c_bool]
    _user32.AttachThreadInput.restype = ctypes.c_bool
    _user32.GetWindowRect.argtypes = [ctypes.c_void_p, ctypes.POINTER(_wt.RECT)]
    _user32.GetWindowRect.restype = ctypes.c_bool
    _user32.GetClassNameW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int]
    _user32.GetClassNameW.restype = ctypes.c_int
    _user32.GetWindowTextW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int]
    _user32.GetWindowTextW.restype = ctypes.c_int
    _user32.GetWindowThreadProcessId.argtypes = [ctypes.c_void_p, ctypes.POINTER(_wt.DWORD)]
    _user32.GetWindowThreadProcessId.restype = ctypes.c_uint
    _user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
    _user32.SetCursorPos.restype = ctypes.c_bool
    _user32.mouse_event.argtypes = [
        ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p
    ]
    _user32.keybd_event.argtypes = [
        ctypes.c_ubyte, ctypes.c_ubyte, ctypes.c_uint, ctypes.c_void_p
    ]
    _user32.GetDpiForWindow.argtypes = [ctypes.c_void_p]
    _user32.GetDpiForWindow.restype = ctypes.c_uint
    _kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
    _kernel32.GlobalAlloc.restype = ctypes.c_void_p
    _kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    _kernel32.GlobalLock.restype = ctypes.c_void_p
    _kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    _kernel32.GlobalUnlock.restype = ctypes.c_bool
    _kernel32.OpenProcess.argtypes = [ctypes.c_uint, ctypes.c_bool, ctypes.c_uint]
    _kernel32.OpenProcess.restype = ctypes.c_void_p
    _kernel32.QueryFullProcessImageNameW.argtypes = [
        ctypes.c_void_p, ctypes.c_uint, ctypes.c_wchar_p, ctypes.POINTER(_wt.DWORD)
    ]
    _kernel32.QueryFullProcessImageNameW.restype = ctypes.c_bool
    _kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    _kernel32.CloseHandle.restype = ctypes.c_bool

    # ---------- clipboard ----------
    def _get_clipboard_text():
        if not _user32.OpenClipboard(0):
            return None
        try:
            handle = _user32.GetClipboardData(_CF_UNICODETEXT)
            if not handle:
                return None
            pointer = _kernel32.GlobalLock(handle)
            if not pointer:
                return None
            try:
                return ctypes.wstring_at(pointer)
            finally:
                _kernel32.GlobalUnlock(handle)
        finally:
            _user32.CloseClipboard()

    def _set_clipboard_text(text):
        data = text.encode("utf-16-le") + b"\x00\x00"
        if not _user32.OpenClipboard(0):
            raise OSError("无法打开剪贴板")
        try:
            _user32.EmptyClipboard()
            handle = _kernel32.GlobalAlloc(_GMEM_MOVEABLE, len(data))
            if not handle:
                raise OSError("GlobalAlloc 失败")
            pointer = _kernel32.GlobalLock(handle)
            try:
                ctypes.memmove(pointer, data, len(data))
            finally:
                _kernel32.GlobalUnlock(handle)
            if not _user32.SetClipboardData(_CF_UNICODETEXT, handle):
                raise OSError("SetClipboardData 失败")
        finally:
            _user32.CloseClipboard()

    # ---------- windows ----------
    def _process_exe(pid):
        handle = _kernel32.OpenProcess(0x1000, False, pid)
        if not handle:
            return ""
        try:
            buffer = ctypes.create_unicode_buffer(1024)
            size = _wt.DWORD(len(buffer))
            if _kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
                return buffer.value
            return ""
        finally:
            _kernel32.CloseHandle(handle)

    def _weixin_windows():
        windows = []

        def callback(hwnd, _lparam):
            pid = _wt.DWORD()
            _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            exe = os.path.basename(_process_exe(pid.value)).lower()
            if exe not in ("weixin.exe", "wechat.exe"):
                return True
            class_name = ctypes.create_unicode_buffer(256)
            _user32.GetClassNameW(hwnd, class_name, 256)
            name = class_name.value
            # WeChat 4.x uses a Qt class; 3.x uses these window classes. Do not
            # require visibility: minimising to the tray hides the main window,
            # and treating that as "WeChat is not running" is what made callers
            # relaunch it and land on the login page.
            if not (
                name.endswith("QWindowIcon")
                or name in ("WeChatMainWndForPC", "WeChatLoginWndForPC")
            ):
                return True
            rect = _wt.RECT()
            if not _user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                return True
            title = ctypes.create_unicode_buffer(512)
            _user32.GetWindowTextW(hwnd, title, 512)
            area = (rect.right - rect.left) * (rect.bottom - rect.top)
            if area <= 0:
                return True
            windows.append(
                {
                    "hwnd": int(hwnd),
                    "left": rect.left,
                    "top": rect.top,
                    "right": rect.right,
                    "bottom": rect.bottom,
                    "width": rect.right - rect.left,
                    "height": rect.bottom - rect.top,
                    "area": area,
                    "visible": bool(_user32.IsWindowVisible(hwnd)),
                    "title": title.value,
                }
            )
            return True

        _user32.EnumWindows(_EnumWindowsProc(callback), 0)
        return windows

    def _find_main_window():
        windows = _weixin_windows()
        if not windows:
            return None

        def named(window):
            title = window["title"].lower()
            return any(k.lower() in title for k in ("微信", "wechat", "weixin"))

        # Prefer the visible WeChat main window, then any visible window, then
        # a hidden one (minimised to the tray). _activate() restores a hidden
        # window instead of starting a second WeChat and losing the session.
        for pool in (
            [w for w in windows if w["visible"] and named(w)],
            [w for w in windows if w["visible"]],
            [w for w in windows if named(w)],
            windows,
        ):
            if pool:
                return max(pool, key=lambda w: w["area"])["hwnd"]

    def _weixin_process_running():
        """True when Weixin.exe/WeChat.exe exists, even with no window."""
        TH32CS_SNAPPROCESS = 0x00000002
        INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

        class PROCESSENTRY32W(ctypes.Structure):
            _fields_ = [
                ("dwSize", _wt.DWORD),
                ("cntUsage", _wt.DWORD),
                ("th32ProcessID", _wt.DWORD),
                ("th32DefaultHeapID", ctypes.c_void_p),
                ("th32ModuleID", _wt.DWORD),
                ("cntThreads", _wt.DWORD),
                ("th32ParentProcessID", _wt.DWORD),
                ("pcPriClassBase", ctypes.c_long),
                ("dwFlags", _wt.DWORD),
                ("szExeFile", ctypes.c_wchar * 260),
            ]

        _kernel32.CreateToolhelp32Snapshot.argtypes = [ctypes.c_uint, ctypes.c_uint]
        _kernel32.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
        _kernel32.Process32FirstW.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(PROCESSENTRY32W),
        ]
        _kernel32.Process32FirstW.restype = ctypes.c_bool
        _kernel32.Process32NextW.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(PROCESSENTRY32W),
        ]
        _kernel32.Process32NextW.restype = ctypes.c_bool

        snapshot = _kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if not snapshot or snapshot == INVALID_HANDLE_VALUE:
            return False
        try:
            entry = PROCESSENTRY32W()
            entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
            if not _kernel32.Process32FirstW(snapshot, ctypes.byref(entry)):
                return False
            while True:
                if entry.szExeFile.lower() in ("weixin.exe", "wechat.exe"):
                    return True
                if not _kernel32.Process32NextW(snapshot, ctypes.byref(entry)):
                    return False
        finally:
            _kernel32.CloseHandle(snapshot)

    def _window_rect(hwnd):
        rect = _wt.RECT()
        _user32.GetWindowRect(hwnd, ctypes.byref(rect))
        return rect

    # ---------- activation and input ----------
    def _activate(hwnd):
        if _user32.GetForegroundWindow() == hwnd:
            return True
        foreground = _user32.GetForegroundWindow()
        foreground_tid = _user32.GetWindowThreadProcessId(foreground, None)
        current_tid = _kernel32.GetCurrentThreadId()
        _user32.AttachThreadInput(foreground_tid, current_tid, True)
        _user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        _user32.SetForegroundWindow(hwnd)
        _user32.AttachThreadInput(foreground_tid, current_tid, False)
        time.sleep(0.6)
        if _user32.GetForegroundWindow() == hwnd:
            return True
        # Windows may refuse foreground changes; a lone ALT keypress lifts that.
        _user32.keybd_event(_VK_ALT, 0, 0, 0)
        _user32.keybd_event(_VK_ALT, 0, 2, 0)
        _user32.SetForegroundWindow(hwnd)
        time.sleep(0.4)
        return _user32.GetForegroundWindow() == hwnd

    def _key(vk, up=False):
        _user32.keybd_event(vk, 0, 0x0002 if up else 0, 0)

    def _press(vk, times=1, delay=0.04):
        for _ in range(times):
            _key(vk)
            time.sleep(0.02)
            _key(vk, True)
            time.sleep(delay)

    def _combo(modifier, key):
        _key(modifier)
        time.sleep(0.03)
        _key(key)
        time.sleep(0.05)
        _key(key, True)
        _key(modifier, True)
        time.sleep(0.1)

    def _click_screen(x, y):
        _user32.SetCursorPos(int(x), int(y))
        time.sleep(0.12)
        _user32.mouse_event(0x0002, 0, 0, 0, 0)  # LEFTDOWN
        time.sleep(0.05)
        _user32.mouse_event(0x0004, 0, 0, 0, 0)  # LEFTUP

    def _window_scale(hwnd):
        try:
            dpi = _user32.GetDpiForWindow(hwnd)
        except AttributeError:
            dpi = 96
        return (dpi or 96) / 96.0

    def _click_96(hwnd, x96, y96):
        rect = _window_rect(hwnd)
        scale = _window_scale(hwnd)
        _click_screen(rect.left + x96 * scale, rect.top + y96 * scale)

    def _click_ratio(hwnd, fx, fy):
        rect = _window_rect(hwnd)
        _click_screen(
            rect.left + (rect.right - rect.left) * fx,
            rect.top + (rect.bottom - rect.top) * fy,
        )

    # ---------- OCR (macOS equivalent of screencapture + Vision) ----------
    async def _ocr_file_async(path, language_tag):
        file = await _StorageFile.get_file_from_path_async(path)
        stream = await file.open_async(_FileAccessMode.READ)
        decoder = await _BitmapDecoder.create_async(stream)
        bitmap = await decoder.get_software_bitmap_async()
        engine = _OcrEngine.try_create_from_language(_Language(language_tag))
        if engine is None:
            engine = _OcrEngine.try_create_from_user_profile_languages()
        if engine is None:
            raise RuntimeError("Windows OCR 不可用，请安装中文 OCR 语言包")
        return await engine.recognize_async(bitmap)

    def _ocr_window(hwnd):
        """Screenshot the window region and OCR it, like macOS does."""
        if ImageGrab is None or _OcrEngine is None:
            raise RuntimeError("缺少依赖：请运行 pip install winsdk pillow")
        rect = _window_rect(hwnd)
        image = ImageGrab.grab(
            bbox=(rect.left, rect.top, rect.right, rect.bottom), all_screens=True
        )
        path = os.path.join(tempfile.gettempdir(), "wechat-agent-ocr.png")
        image.save(path)
        result = asyncio.run(_ocr_file_async(path, "zh-Hans"))
        lines = []
        for line in result.lines:
            words = list(line.words)
            if not words:
                continue
            boxes = [word.bounding_rect for word in words]
            lines.append(
                {
                    "text": line.text,
                    "x0": min(box.x for box in boxes),
                    "y0": min(box.y for box in boxes),
                    "x1": max(box.x + box.width for box in boxes),
                    "y1": max(box.y + box.height for box in boxes),
                }
            )
        return lines, (image.width, image.height)

    def _norm(text):
        return "".join(text.split()).lower()

    def _topmost_match(lines, target, top_limit=0):
        wanted = _norm(target)
        matches = [
            line
            for line in lines
            if line["y0"] > top_limit and wanted in _norm(line["text"])
        ]
        if not matches:
            return None
        return min(matches, key=lambda line: line["y0"])

    def _find_contact_line(lines, name, top_limit=0):
        """Same idea as macOS find_and_click: click the "微信 ClawBot" row."""
        for marker in ("微信 ClawBot", "ClawBot", name):
            match = _topmost_match(lines, marker, top_limit)
            if match is not None:
                return match
        return None

    def _chat_title_matches(hwnd, name):
        """Guard against sending into the wrong chat.

        OCR often misreads a Chinese character or two (e.g. "总结" ->
        "，总结吉"), so accept a close match instead of an exact one.
        """
        lines, (width, height) = _ocr_window(hwnd)
        target = _norm(name)
        for line in lines:
            if line["y0"] >= height * 0.14 or line["x0"] <= width * 0.32:
                continue
            text = _norm(line["text"])
            if target in text:
                return True
            if difflib.SequenceMatcher(None, target, text).ratio() >= 0.6:
                return True
        return False

    # ---------- main flow ----------
    def send_via_ui_windows(cfg, message, dry_run=False):
        name = (cfg.get("wechat_name") or "").strip()
        if not name:
            sys.exit("配置缺少 wechat_name（微信里显示的对话名称）")
        if ImageGrab is None or _OcrEngine is None:
            sys.exit("缺少依赖：请运行 pip install winsdk pillow")

        _user32.SetProcessDPIAware()
        hwnd = _find_main_window()
        if not hwnd:
            if _weixin_process_running():
                sys.exit(
                    "检测到微信正在运行，但主窗口在后台或托盘里。\n"
                    "请手动点击托盘/任务栏的微信图标打开主窗口后重试。\n"
                    "不要重新启动微信——重复启动会进入登录页。"
                )
            sys.exit(
                "微信未运行。请手动启动并登录微信桌面客户端后重试。\n"
                "脚本不会自动启动微信。"
            )
        if not _activate(hwnd):
            sys.exit("无法激活微信窗口，请手动切换到微信后重试（不要重新启动微信）")

        def ensure_foreground():
            if _user32.GetForegroundWindow() == hwnd:
                return True
            return _activate(hwnd)

        old_clipboard = _get_clipboard_text()
        try:
            # 1. focus the search box, clear stale text, enter the name
            if not ensure_foreground():
                sys.exit("微信窗口不在前台，已中止发送")
            _click_96(hwnd, 167, 59)
            time.sleep(0.5)
            if not ensure_foreground():
                sys.exit("微信窗口不在前台，已中止发送")
            _combo(_VK_CONTROL, _VK_A)
            _press(_VK_BACK)
            time.sleep(0.3)
            _set_clipboard_text(name)
            time.sleep(0.15)
            _combo(_VK_CONTROL, _VK_V)
            time.sleep(1.6)

            # 2. screenshot + OCR, then click the conversation row
            if not ensure_foreground():
                sys.exit("微信窗口不在前台，已中止发送")
            lines, (width, height) = _ocr_window(hwnd)
            scale = _window_scale(hwnd)
            contact = _find_contact_line(lines, name, 70 * scale)
            if contact is None:
                sys.exit(
                    "在搜索结果中找不到对话「%s」，已中止发送。\n"
                    "若微信停在登录页，请先完成登录；不要重复启动微信。" % name
                )
            rect = _window_rect(hwnd)
            _click_screen(
                rect.left + (contact["x0"] + contact["x1"]) / 2,
                rect.top + (contact["y0"] + contact["y1"]) / 2,
            )
            time.sleep(1.4)

            # 3. verify the opened chat before sending anything
            if not _chat_title_matches(hwnd, name):
                sys.exit(
                    "打开的对话不是「%s」，已中止发送。\n"
                    "若微信停在登录页，请先完成登录；不要重复启动微信。" % name
                )

            # 4. focus the message box, paste the report, send
            if not ensure_foreground():
                sys.exit("微信窗口不在前台，已中止发送")
            _click_ratio(hwnd, 0.55, 0.84)
            time.sleep(0.3)
            if not ensure_foreground():
                sys.exit("微信窗口不在前台，已中止发送")
            _combo(_VK_CONTROL, _VK_A)
            _press(_VK_BACK)
            time.sleep(0.2)
            _set_clipboard_text(message)
            time.sleep(0.15)
            _combo(_VK_CONTROL, _VK_V)
            time.sleep(0.4)
            if dry_run:
                print("dry run：已定位对话并填入消息，未按回车发送。", file=sys.stderr)
                return
            if not ensure_foreground():
                sys.exit("微信窗口不在前台，已中止发送")
            _press(_VK_RETURN)
            time.sleep(0.8)
        finally:
            if old_clipboard is not None:
                try:
                    _set_clipboard_text(old_clipboard)
                except OSError:
                    pass


def resolve_template(config_path, cfg):
    ref = cfg.get("reference")
    if ref:
        base = os.path.dirname(os.path.abspath(config_path))
        path = ref if os.path.isabs(ref) else os.path.join(base, ref)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return f.read().strip("\n")
        print("警告：找不到 reference %s，改用 format" % path, file=sys.stderr)
    return cfg.get("format", DEFAULT_FORMAT)


def send_via_ui_macos(cfg, message):
    name = (cfg.get("wechat_name") or "").strip()
    if not name:
        sys.exit("配置缺少 wechat_name（微信里显示的对话名称）")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env = os.environ.copy()
    name_fd, name_path = tempfile.mkstemp(prefix="wechat-name-", suffix=".txt")
    msg_fd, msg_path = tempfile.mkstemp(prefix="wechat-msg-", suffix=".txt")
    try:
        with os.fdopen(name_fd, "w", encoding="utf-8") as f:
            f.write(name)
        with os.fdopen(msg_fd, "w", encoding="utf-8") as f:
            f.write(message)
        env["WECHAT_AGENT_NAME_FILE"] = name_path
        env["WECHAT_AGENT_MESSAGE_FILE"] = msg_path
        result = subprocess.run(
            ["bash", os.path.join(script_dir, "send_ui_macos.sh")], env=env
        )
        if result.returncode != 0:
            sys.exit("界面发送失败，退出码 %d" % result.returncode)
    finally:
        for path in (name_path, msg_path):
            try:
                os.remove(path)
            except OSError:
                pass


def send_via_ui(cfg, message, dry_run=False):
    if sys.platform == "darwin":
        if dry_run:
            sys.exit("macOS 暂不支持 --dry-run")
        send_via_ui_macos(cfg, message)
    elif sys.platform.startswith("win"):
        send_via_ui_windows(cfg, message, dry_run)
    else:
        sys.exit("仅支持 macOS 和 Windows")


def load_config(path):
    if not os.path.exists(path):
        sys.exit("配置文件不存在：%s\n请先运行 install.sh 或手动创建。" % path)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_message(fmt, project, title, background, summary, special, now, device):
    fields = {
        "{project}": project,
        "{title}": title,
        "{background}": background,
        "{summary}": summary,
        "{special}": special or "",
        "{time}": now,
        "{device}": device,
    }
    lines = []
    for line in fmt.split("\n"):
        if "{special}" in line and not special:
            continue
        for placeholder, value in fields.items():
            line = line.replace(placeholder, value)
        lines.append(line)
    return "\n".join(lines)


def cmd_list(config):
    agents = config.get("agents", {})
    if not agents:
        print("没有配置任何 agent")
        return
    for name, cfg in agents.items():
        print("%s\t%s" % (name, cfg.get("wechat_name") or cfg.get("clawbot_dir", "")))


def _use_utf8_when_captured():
    """Claude Code captures stdout as a pipe and decodes it as UTF-8.

    Windows would otherwise emit GBK there and garble every Chinese line,
    including the --check preview the caller is supposed to inspect. Leave an
    interactive console alone so cmd keeps displaying Chinese correctly.
    """
    if not sys.platform.startswith("win"):
        return
    for stream in (sys.stdout, sys.stderr):
        try:
            if not stream.isatty():
                stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError, ValueError):
            pass


def main():
    parser = argparse.ArgumentParser(description="向配置好的微信 agent 对话发送任务完成报告")
    parser.add_argument("--config", default=os.environ.get("WECHAT_AGENT_REPORT_CONFIG", DEFAULT_CONFIG))
    parser.add_argument("--list", action="store_true", help="列出已配置的 agent")
    parser.add_argument("--agent", help="agent 名称")
    parser.add_argument("--project", help="项目名（必填，用于标题）")
    parser.add_argument("--title", help="本次做了什么（必填）")
    parser.add_argument("--background", help="项目背景（必填，一句话说明这是什么项目）")
    parser.add_argument("--summary", help="完成内容摘要")
    parser.add_argument("--file", help="从文件读取摘要")
    parser.add_argument("--special", default="", help="特别指示（可选）")
    parser.add_argument("--time", default=None, help="时间，默认当前时间")
    parser.add_argument("--check", action="store_true", help="只生成并打印消息与字数，不发送")
    parser.add_argument("--dry-run", action="store_true", help="只定位对话并填入消息，不发送")
    args = parser.parse_args()

    config = load_config(args.config)
    if args.list:
        cmd_list(config)
        return 0

    if not args.agent:
        sys.exit("需要 --agent")
    project = (args.project or "").strip()
    title = (args.title or "").strip()
    background = (args.background or "").strip()
    if not project:
        sys.exit("需要 --project（项目名，例如 SMALL SILENT HUMAN）")
    if not title:
        sys.exit("需要 --title（本次做了什么）")
    if not background:
        sys.exit("需要 --background（一句话说明项目是什么，写给没看过这个项目的人）")
    if background == project:
        sys.exit("--background 不能只填项目名，请写清项目是什么（本次未发送）")

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

    template = resolve_template(args.config, cfg)
    missing = [p for p in REQUIRED_PLACEHOLDERS if p not in template]
    if missing:
        sys.exit(
            "模板缺少占位符 %s：请更新 %s 中的提交模板（本次未发送）"
            % ("、".join(missing), args.config)
        )

    limit = int(cfg.get("max_words", 200))
    used = len(background) + len(summary)
    if used > limit:
        sys.exit(
            "内容超长：背景 %d 字 + 摘要 %d 字 = %d 字，超过 %d 字上限。\n"
            "请压缩摘要后重试（本次未发送；不要依赖截断，接收方会看到残缺内容）。"
            % (len(background), len(summary), used, limit)
        )

    now = args.time or datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    device = socket.gethostname().split(".")[0]
    message = build_message(
        template,
        project,
        title,
        background,
        summary,
        args.special.strip(),
        now,
        device,
    )

    if args.check:
        print(message)
        print()
        print(
            "— 背景 %d 字 + 摘要 %d 字 = %d / %d 字（未发送）"
            % (len(background), len(summary), used, limit)
        )
        return 0

    send_via_ui(cfg, message, args.dry_run)

    if args.dry_run:
        print("dry run 完成（未发送）：%s" % title)
    else:
        print("已发送给 %s：%s" % (args.agent, title))
    return 0


if __name__ == "__main__":
    _use_utf8_when_captured()
    sys.exit(main())
