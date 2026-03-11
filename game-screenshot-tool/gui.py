"""GUI設定画面 - tkinterベースの設定UIとシステムトレイ常駐"""

import json
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path


CONFIG_PATH = Path(__file__).parent / "config.json"

DEFAULT_CONFIG = {
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


def load_config():
    """設定ファイルを読み込む"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        # デフォルト値を補完
        for key, value in DEFAULT_CONFIG.items():
            config.setdefault(key, value)
        return config
    return DEFAULT_CONFIG.copy()


def save_config(config):
    """設定ファイルに保存する"""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


class HotkeyRecorder:
    """ホットキー入力を記録するウィジェット"""

    def __init__(self, parent, current_hotkey):
        self.frame = ttk.Frame(parent)
        self.hotkey = current_hotkey
        self.recording = False

        self.label = ttk.Label(self.frame, text=current_hotkey, width=25,
                               relief="sunken", anchor="center", padding=5)
        self.label.pack(side="left", padx=(0, 5))

        self.btn = ttk.Button(self.frame, text="変更", command=self._toggle_record)
        self.btn.pack(side="left")

        self.label.bind("<KeyPress>", self._on_key)
        self.label.bind("<FocusOut>", self._stop_record)

    def _toggle_record(self):
        if self.recording:
            self._stop_record()
        else:
            self.recording = True
            self.label.configure(text="キーを押してください...")
            self.btn.configure(text="キャンセル")
            self.label.focus_set()

    def _on_key(self, event):
        if not self.recording:
            return

        parts = []
        if event.state & 0x4:
            parts.append("ctrl")
        if event.state & 0x8:
            parts.append("alt")
        if event.state & 0x1:
            parts.append("shift")

        key = event.keysym
        # 修飾キー単体は無視
        if key in ("Control_L", "Control_R", "Alt_L", "Alt_R",
                    "Shift_L", "Shift_R"):
            return

        # 特殊キー名を keyboard ライブラリの形式に変換
        key_map = {
            "Print": "PrintScreen",
            "Return": "enter",
            "Escape": "esc",
            "BackSpace": "backspace",
            "Delete": "delete",
            "space": "space",
        }
        key = key_map.get(key, key.lower())

        if parts:
            self.hotkey = "+".join(parts) + "+" + key
        else:
            self.hotkey = key

        self._stop_record()

    def _stop_record(self, event=None):
        self.recording = False
        self.label.configure(text=self.hotkey)
        self.btn.configure(text="変更")

    def get(self):
        return self.hotkey


class AliasEditor:
    """プロセス名エイリアスの編集UI"""

    def __init__(self, parent, aliases):
        self.frame = ttk.LabelFrame(parent, text="ゲーム名エイリアス", padding=10)
        self.aliases = dict(aliases)

        # テーブル
        columns = ("process", "display")
        self.tree = ttk.Treeview(self.frame, columns=columns, show="headings",
                                 height=5)
        self.tree.heading("process", text="プロセス名 (exe)")
        self.tree.heading("display", text="表示名")
        self.tree.column("process", width=200)
        self.tree.column("display", width=200)
        self.tree.pack(fill="both", expand=True, pady=(0, 5))

        # スクロールバー
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical",
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # ボタン行
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill="x")

        ttk.Button(btn_frame, text="追加", command=self._add).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="編集", command=self._edit).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="削除", command=self._delete).pack(side="left", padx=2)

        self._refresh()

    def _refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for proc, display in self.aliases.items():
            self.tree.insert("", "end", values=(proc, display))

    def _add(self):
        dialog = _AliasDialog(self.frame.winfo_toplevel(), "エイリアス追加")
        if dialog.result:
            proc, display = dialog.result
            self.aliases[proc] = display
            self._refresh()

    def _edit(self):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0], "values")
        dialog = _AliasDialog(self.frame.winfo_toplevel(), "エイリアス編集",
                               values[0], values[1])
        if dialog.result:
            del self.aliases[values[0]]
            proc, display = dialog.result
            self.aliases[proc] = display
            self._refresh()

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0], "values")
        del self.aliases[values[0]]
        self._refresh()

    def get(self):
        return dict(self.aliases)


class _AliasDialog:
    """エイリアス追加/編集ダイアログ"""

    def __init__(self, parent, title, process="", display=""):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.resizable(False, False)
        self.dialog.grab_set()

        frame = ttk.Frame(self.dialog, padding=15)
        frame.pack()

        ttk.Label(frame, text="プロセス名 (例: game.exe):").grid(
            row=0, column=0, sticky="w", pady=2)
        self.proc_var = tk.StringVar(value=process)
        ttk.Entry(frame, textvariable=self.proc_var, width=35).grid(
            row=0, column=1, pady=2, padx=(5, 0))

        ttk.Label(frame, text="表示名 (例: Game Title):").grid(
            row=1, column=0, sticky="w", pady=2)
        self.display_var = tk.StringVar(value=display)
        ttk.Entry(frame, textvariable=self.display_var, width=35).grid(
            row=1, column=1, pady=2, padx=(5, 0))

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(btn_frame, text="OK", command=self._ok).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="キャンセル",
                   command=self.dialog.destroy).pack(side="left", padx=5)

        self.dialog.wait_window()

    def _ok(self):
        proc = self.proc_var.get().strip()
        display = self.display_var.get().strip()
        if proc and display:
            self.result = (proc, display)
            self.dialog.destroy()


class SettingsWindow:
    """メイン設定ウィンドウ"""

    def __init__(self, root, config, on_save=None, on_start=None, on_stop=None):
        self.root = root
        self.config = config
        self.on_save = on_save
        self.on_start = on_start
        self.on_stop = on_stop
        self.is_running = False

        root.title("Game Screenshot Tool")
        root.resizable(False, False)

        # メインフレーム
        main = ttk.Frame(root, padding=15)
        main.pack(fill="both", expand=True)

        # === 基本設定 ===
        basic_frame = ttk.LabelFrame(main, text="基本設定", padding=10)
        basic_frame.pack(fill="x", pady=(0, 10))

        # ホットキー
        ttk.Label(basic_frame, text="ショートカットキー:").grid(
            row=0, column=0, sticky="w", pady=3)
        self.hotkey_recorder = HotkeyRecorder(basic_frame, config.get("hotkey", "PrintScreen"))
        self.hotkey_recorder.frame.grid(row=0, column=1, sticky="w", pady=3)

        # 保存先
        ttk.Label(basic_frame, text="保存先フォルダ:").grid(
            row=1, column=0, sticky="w", pady=3)
        dir_frame = ttk.Frame(basic_frame)
        dir_frame.grid(row=1, column=1, sticky="w", pady=3)
        self.save_dir_var = tk.StringVar(
            value=os.path.expanduser(config.get("save_directory", "~/Pictures/GameScreenshots")))
        ttk.Entry(dir_frame, textvariable=self.save_dir_var, width=30).pack(
            side="left", padx=(0, 5))
        ttk.Button(dir_frame, text="参照", command=self._browse_dir).pack(side="left")

        # JPG画質
        ttk.Label(basic_frame, text="JPG画質:").grid(
            row=2, column=0, sticky="w", pady=3)
        quality_frame = ttk.Frame(basic_frame)
        quality_frame.grid(row=2, column=1, sticky="w", pady=3)
        self.quality_var = tk.IntVar(value=config.get("jpg_quality", 95))
        self.quality_scale = ttk.Scale(quality_frame, from_=1, to=100,
                                       variable=self.quality_var, orient="horizontal",
                                       length=200, command=self._update_quality_label)
        self.quality_scale.pack(side="left")
        self.quality_label = ttk.Label(quality_frame, text=str(self.quality_var.get()),
                                       width=4)
        self.quality_label.pack(side="left", padx=(5, 0))

        # === 通知設定 ===
        notify_frame = ttk.LabelFrame(main, text="通知設定", padding=10)
        notify_frame.pack(fill="x", pady=(0, 10))

        self.notification_var = tk.BooleanVar(value=config.get("notification", True))
        ttk.Checkbutton(notify_frame, text="トースト通知を表示",
                        variable=self.notification_var).pack(anchor="w")

        self.sound_var = tk.BooleanVar(value=config.get("sound", False))
        ttk.Checkbutton(notify_frame, text="撮影音を再生",
                        variable=self.sound_var).pack(anchor="w")

        # === ゲーム検出設定 ===
        detect_frame = ttk.LabelFrame(main, text="ゲーム検出", padding=10)
        detect_frame.pack(fill="x", pady=(0, 10))

        detection_config = config.get("game_detection", {})
        self.use_process_var = tk.BooleanVar(
            value=detection_config.get("use_process_name", True))
        ttk.Checkbutton(detect_frame, text="プロセス名で検出",
                        variable=self.use_process_var).pack(anchor="w")

        self.use_title_var = tk.BooleanVar(
            value=detection_config.get("use_window_title", True))
        ttk.Checkbutton(detect_frame, text="ウィンドウタイトルで検出",
                        variable=self.use_title_var).pack(anchor="w")

        # エイリアスエディタ
        self.alias_editor = AliasEditor(
            main, detection_config.get("process_name_aliases", {}))
        self.alias_editor.frame.pack(fill="both", expand=True, pady=(0, 10))

        # === ボタン行 ===
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill="x")

        self.start_btn = ttk.Button(btn_frame, text="開始",
                                    command=self._toggle_capture)
        self.start_btn.pack(side="left", padx=(0, 5))

        ttk.Button(btn_frame, text="保存", command=self._save).pack(side="left", padx=5)

        self.status_label = ttk.Label(btn_frame, text="停止中", foreground="gray")
        self.status_label.pack(side="right")

        # トレイに最小化
        ttk.Button(btn_frame, text="トレイに格納",
                   command=self._minimize_to_tray).pack(side="right", padx=5)

        # ウィンドウを閉じるときの処理
        root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _update_quality_label(self, value):
        self.quality_label.configure(text=str(int(float(value))))

    def _browse_dir(self):
        path = filedialog.askdirectory(initialdir=self.save_dir_var.get())
        if path:
            self.save_dir_var.set(path)

    def _build_config(self):
        """UIの値から設定辞書を構築する"""
        config = dict(self.config)
        config["hotkey"] = self.hotkey_recorder.get()
        config["save_directory"] = self.save_dir_var.get()
        config["jpg_quality"] = int(self.quality_var.get())
        config["notification"] = self.notification_var.get()
        config["sound"] = self.sound_var.get()

        detection = config.get("game_detection", {})
        detection["use_process_name"] = self.use_process_var.get()
        detection["use_window_title"] = self.use_title_var.get()
        detection["process_name_aliases"] = self.alias_editor.get()
        config["game_detection"] = detection

        return config

    def _save(self):
        self.config = self._build_config()
        save_config(self.config)
        if self.on_save:
            self.on_save(self.config)
        messagebox.showinfo("保存完了", "設定を保存しました。")

    def _toggle_capture(self):
        if self.is_running:
            self.is_running = False
            self.start_btn.configure(text="開始")
            self.status_label.configure(text="停止中", foreground="gray")
            if self.on_stop:
                self.on_stop()
        else:
            self.config = self._build_config()
            save_config(self.config)
            self.is_running = True
            self.start_btn.configure(text="停止")
            self.status_label.configure(text="撮影待機中", foreground="green")
            if self.on_start:
                self.on_start(self.config)

    def _minimize_to_tray(self):
        self.root.withdraw()

    def show(self):
        self.root.deiconify()
        self.root.lift()

    def _on_close(self):
        if self.is_running:
            result = messagebox.askyesnocancel(
                "終了確認",
                "撮影中です。\n「はい」→ 終了\n「いいえ」→ トレイに格納")
            if result is True:
                self.root.quit()
            elif result is False:
                self._minimize_to_tray()
            # Noneの場合はキャンセル
        else:
            self.root.quit()
