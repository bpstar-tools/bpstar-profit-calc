"""ゲームスクリーンショットツール - GUI付きのメインエントリーポイント"""

import ctypes
import ctypes.wintypes
import os
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path

import keyboard
from PIL import ImageGrab

from game_detector import detect_game_name
from gui import SettingsWindow, load_config, save_config
from tray import setup_tray


class ScreenshotApp:
    """アプリケーション全体を管理するクラス"""

    def __init__(self):
        self.config = load_config()
        self.is_running = False
        self.hotkey_hook = None

        # tkinter ルートウィンドウ
        self.root = tk.Tk()
        self.root.withdraw()  # 初期は非表示

        # 設定ウィンドウ
        self.settings_window = None
        self._show_settings()

    def _show_settings(self):
        """設定ウィンドウを表示する"""
        if self.settings_window is None:
            settings_root = tk.Toplevel(self.root)
            self.settings_window = SettingsWindow(
                settings_root,
                self.config,
                on_save=self._on_config_save,
                on_start=self._start_capture,
                on_stop=self._stop_capture,
            )
            settings_root.protocol("WM_DELETE_WINDOW", self._on_settings_close)
        else:
            self.settings_window.show()

    def _on_settings_close(self):
        """設定ウィンドウの閉じるボタン処理"""
        self.settings_window._on_close()

    def _on_config_save(self, config):
        """設定保存時のコールバック"""
        self.config = config

    def _start_capture(self, config):
        """スクリーンショット撮影を開始する"""
        self.config = config
        self.is_running = True

        # 既存のホットキーを解除
        if self.hotkey_hook is not None:
            keyboard.unhook_all_hotkeys()

        hotkey = config.get("hotkey", "PrintScreen")
        self.hotkey_hook = keyboard.add_hotkey(
            hotkey, self._on_hotkey, suppress=True
        )

    def _stop_capture(self):
        """スクリーンショット撮影を停止する"""
        self.is_running = False
        if self.hotkey_hook is not None:
            keyboard.unhook_all_hotkeys()
            self.hotkey_hook = None

    def _on_hotkey(self):
        """ホットキー押下時のコールバック"""
        thread = threading.Thread(target=self._take_screenshot, daemon=True)
        thread.start()

    def _take_screenshot(self):
        """スクリーンショットを撮影して保存する"""
        monitor_rect = self._get_active_monitor_rect()
        if not monitor_rect:
            return

        screenshot = ImageGrab.grab(bbox=monitor_rect)
        game_name = detect_game_name(self.config)

        save_dir = Path(os.path.expanduser(self.config["save_directory"])) / game_name
        save_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime(self.config.get("timestamp_format", "%Y%m%d_%H%M%S"))
        filename = f"{timestamp}.jpg"
        filepath = save_dir / filename

        counter = 1
        while filepath.exists():
            filename = f"{timestamp}_{counter}.jpg"
            filepath = save_dir / filename
            counter += 1

        screenshot.save(filepath, "JPEG", quality=self.config.get("jpg_quality", 95))

        if self.config.get("notification", True):
            self._show_notification(game_name, str(filepath))

        if self.config.get("sound", False):
            self._play_capture_sound()

    @staticmethod
    def _get_active_monitor_rect():
        """アクティブウィンドウが表示されているモニターの領域を取得する"""
        user32 = ctypes.windll.user32

        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return None

        MONITOR_DEFAULTTONEAREST = 2
        hmonitor = user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)

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

    @staticmethod
    def _show_notification(game_name, filepath):
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
            pass

    @staticmethod
    def _play_capture_sound():
        """撮影音を再生する"""
        try:
            import winsound
            winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
        except Exception:
            pass

    def _setup_tray(self):
        """システムトレイアイコンをセットアップする"""
        def on_show():
            self.root.after(0, self._show_settings)

        def on_toggle():
            def _toggle():
                if self.is_running:
                    self._stop_capture()
                    if self.settings_window:
                        self.settings_window.is_running = False
                        self.settings_window.start_btn.configure(text="開始")
                        self.settings_window.status_label.configure(
                            text="停止中", foreground="gray")
                else:
                    self._start_capture(self.config)
                    if self.settings_window:
                        self.settings_window.is_running = True
                        self.settings_window.start_btn.configure(text="停止")
                        self.settings_window.status_label.configure(
                            text="撮影待機中", foreground="green")
            self.root.after(0, _toggle)

        def on_quit():
            self._stop_capture()
            if self.tray_icon:
                self.tray_icon.stop()
            self.root.after(0, self.root.quit)

        self.tray_icon = setup_tray(
            on_show_settings=on_show,
            on_toggle_capture=on_toggle,
            on_quit=on_quit,
            is_running_fn=lambda: self.is_running,
        )

        # トレイアイコンは別スレッドで実行
        tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        tray_thread.start()

    def run(self):
        """アプリケーションを起動する"""
        self._setup_tray()
        self.root.mainloop()

        # 終了処理
        self._stop_capture()
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass


def main():
    app = ScreenshotApp()
    app.run()


if __name__ == "__main__":
    main()
