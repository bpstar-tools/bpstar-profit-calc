"""システムトレイアイコン - pystrayベースのトレイ常駐"""

import threading

from PIL import Image, ImageDraw


def create_tray_icon():
    """カメラ風のトレイアイコン画像を生成する"""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # カメラ本体
    draw.rounded_rectangle([4, 16, 60, 52], radius=6, fill="#2196F3", outline="#1565C0", width=2)
    # レンズ
    draw.ellipse([20, 22, 44, 46], fill="#1565C0", outline="#0D47A1", width=2)
    draw.ellipse([26, 28, 38, 40], fill="#64B5F6")
    # フラッシュ部分
    draw.rectangle([18, 10, 30, 18], fill="#2196F3", outline="#1565C0", width=1)

    return img


def setup_tray(on_show_settings, on_toggle_capture, on_quit, is_running_fn):
    """システムトレイアイコンをセットアップして返す

    Args:
        on_show_settings: 設定画面を表示するコールバック
        on_toggle_capture: 撮影の開始/停止を切り替えるコールバック
        on_quit: アプリケーション終了コールバック
        is_running_fn: 撮影中かどうかを返す関数
    """
    import pystray

    icon_image = create_tray_icon()

    def create_menu():
        running = is_running_fn()
        return pystray.Menu(
            pystray.MenuItem(
                "撮影停止" if running else "撮影開始",
                lambda: on_toggle_capture(),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("設定", lambda: on_show_settings()),
            pystray.MenuItem("終了", lambda: on_quit()),
        )

    icon = pystray.Icon(
        "GameScreenshot",
        icon_image,
        "Game Screenshot Tool",
        menu=create_menu(),
    )

    # メニューを動的に更新するため、メニュー生成関数を設定
    icon.menu = create_menu

    return icon
