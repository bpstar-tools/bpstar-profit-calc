"""PyInstallerでexeをビルドするスクリプト"""

import subprocess
import sys


def build():
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "GameScreenshotTool",
        "--onefile",
        "--windowed",
        "--add-data", "config.json;.",
        "--icon", "NONE",
        "screenshot_tool.py",
    ]

    print("ビルド開始...")
    print(f"コマンド: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    print("\nビルド完了! dist/GameScreenshotTool.exe が生成されました。")


if __name__ == "__main__":
    build()
