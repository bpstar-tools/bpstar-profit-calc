"""ゲームスクリーンショットツール - ショートカットキーでアクティブモニターを撮影"""

import ctypes
import ctypes.wintypes
import json
import os
import sys
import threading
from datetime import datetime
from pathlib import Path

import keyboard
from PIL import Image, ImageGrab

from game_detector import detect_game_name


def load_config():
    """設定ファイルを読み込む。存在しない場合はデフォルト設定を使用する"""
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    return {
        "hotkey": "PrintScreen",
        "save_directory": "~/Pictures/GameScreenshots",
        "jpg_quality": 95,
        "notification": True,
        "sound": False,
        "timestamp_format": "%Y%m%d_%H%M%S",
        "game_detection": {
            "use_process_name": True,
            "use_window_title": True,
            "title_cleanup_patterns": [" - ", " \\| ", " \\(.*\\)$"],
            "process_name_aliases": {},
        },
    }


def get_active_monitor_rect():
    """アクティブウィンドウが表示されているモニターの領域を取得する"""
    user32 = ctypes.windll.user32

    # アクティブウィンドウのハンドルを取得
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None

    # ウィンドウが存在するモニターを取得
    MONITOR_DEFAULTTONEAREST = 2
    hmonitor = user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)

    # モニター情報を取得
    class MONITORINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", ctypes.wintypes.DWORD),
            ("rcMonitor", ctypes.wintypes.RECT),
            ("rcWork", ctypes.wintypes.RECT),
            ("dwFlags", ctypes.wintypes.DWORD),
        ]

    mi = MONITORINFO()
    mi.cbSize = ctypes.sizeof(MONITORINFO)
    if not user32.GetMonitorInfoW(hmonitor, ctypes.byref(mi)):
        return None

    rect = mi.rcMonitor
    return (rect.left, rect.top, rect.right, rect.bottom)


def take_screenshot(config):
    """スクリーンショットを撮影して保存する"""
    # アクティブモニターの領域を取得
    monitor_rect = get_active_monitor_rect()
    if not monitor_rect:
        print("[エラー] アクティブモニターを検出できませんでした")
        return

    # スクリーンショット撮影
    screenshot = ImageGrab.grab(bbox=monitor_rect)

    # ゲーム名を検出
    game_name = detect_game_name(config)

    # 保存先ディレクトリを作成
    save_dir = Path(os.path.expanduser(config["save_directory"])) / game_name
    save_dir.mkdir(parents=True, exist_ok=True)

    # ファイル名をタイムスタンプで生成
    timestamp = datetime.now().strftime(config["timestamp_format"])
    filename = f"{timestamp}.jpg"
    filepath = save_dir / filename

    # 同名ファイルが存在する場合は連番を付与
    counter = 1
    while filepath.exists():
        filename = f"{timestamp}_{counter}.jpg"
        filepath = save_dir / filename
        counter += 1

    # JPGで保存
    screenshot.save(filepath, "JPEG", quality=config["jpg_quality"])
    print(f"[保存] {filepath}")

    # 通知
    if config.get("notification", True):
        show_notification(game_name, str(filepath))

    if config.get("sound", False):
        play_capture_sound()


def show_notification(game_name, filepath):
    """Windows トースト通知を表示する"""
    try:
        from win10toast import ToastNotifier

        toaster = ToastNotifier()
        toaster.show_toast(
            "Screenshot Captured",
            f"{game_name}\n{filepath}",
            duration=3,
            threaded=True,
        )
    except ImportError:
        # win10toastが無い場合はコンソール出力のみ
        pass


def play_capture_sound():
    """撮影音を再生する"""
    try:
        import winsound

        winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
    except Exception:
        pass


def main():
    config = load_config()
    hotkey = config.get("hotkey", "PrintScreen")

    print("=== Game Screenshot Tool ===")
    print(f"ホットキー: {hotkey}")
    print(f"保存先: {os.path.expanduser(config['save_directory'])}")
    print(f"JPG画質: {config['jpg_quality']}")
    print("終了するには Ctrl+C を押してください")
    print("---")

    def on_hotkey():
        # メインスレッドをブロックしないようにスレッドで実行
        thread = threading.Thread(target=take_screenshot, args=(config,))
        thread.daemon = True
        thread.start()

    keyboard.add_hotkey(hotkey, on_hotkey, suppress=True)

    try:
        keyboard.wait()
    except KeyboardInterrupt:
        print("\n終了します")


if __name__ == "__main__":
    main()
