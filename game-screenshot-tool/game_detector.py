"""ゲーム検出モジュール - アクティブウィンドウからゲーム名を特定する"""

import re
import ctypes
import ctypes.wintypes


def get_foreground_window_info():
    """アクティブウィンドウのプロセス名とウィンドウタイトルを取得する"""
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None, None

    # ウィンドウタイトル取得
    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    window_title = buf.value

    # プロセスID取得
    pid = ctypes.wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

    # プロセス名取得
    process_name = _get_process_name(kernel32, pid.value)

    return process_name, window_title


def _get_process_name(kernel32, pid):
    """プロセスIDからプロセス名（exe名）を取得する"""
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return None

    try:
        buf = ctypes.create_unicode_buffer(260)
        size = ctypes.wintypes.DWORD(260)
        success = kernel32.QueryFullProcessImageNameW(
            handle, 0, buf, ctypes.byref(size)
        )
        if success:
            # フルパスからファイル名だけ取得
            full_path = buf.value
            return full_path.rsplit("\\", 1)[-1]
        return None
    finally:
        kernel32.CloseHandle(handle)


def detect_game_name(config):
    """設定に基づいてゲーム名を検出する

    Returns:
        str: 検出されたゲーム名（フォルダ名として使用される）
    """
    detection_config = config.get("game_detection", {})
    use_process = detection_config.get("use_process_name", True)
    use_title = detection_config.get("use_window_title", True)
    aliases = detection_config.get("process_name_aliases", {})
    cleanup_patterns = detection_config.get("title_cleanup_patterns", [])

    process_name, window_title = get_foreground_window_info()

    # プロセス名エイリアスをチェック
    if use_process and process_name and process_name in aliases:
        return _sanitize_folder_name(aliases[process_name])

    # プロセス名からゲーム名を生成
    if use_process and process_name:
        game_name = process_name.rsplit(".", 1)[0]  # 拡張子を除去
    elif use_title and window_title:
        game_name = window_title
    else:
        return "Unknown"

    # ウィンドウタイトルでゲーム名を補完
    if use_title and window_title and use_process and process_name:
        # タイトルからノイズを除去
        cleaned_title = window_title
        for pattern in cleanup_patterns:
            cleaned_title = re.split(pattern, cleaned_title)[0].strip()

        if cleaned_title and len(cleaned_title) > len(game_name):
            game_name = cleaned_title

    return _sanitize_folder_name(game_name)


def _sanitize_folder_name(name):
    """フォルダ名として使えない文字を除去する"""
    # Windowsのフォルダ名に使えない文字を置換
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", name)
    sanitized = sanitized.strip(". ")
    return sanitized if sanitized else "Unknown"
