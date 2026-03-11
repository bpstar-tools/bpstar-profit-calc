# Game Screenshot Tool

Windows向けゲームスクリーンショットツール。GUIで設定を管理し、システムトレイに常駐してショートカットキーで撮影できます。

## 機能

- GUI設定画面でショートカットキー・保存先・画質などを変更可能
- システムトレイに常駐（バックグラウンド動作）
- ショートカットキーでアクティブモニターのみを撮影
- ゲーム名を自動検出してフォルダ分け（プロセス名 + ウィンドウタイトル）
- JPG形式で保存（タイムスタンプファイル名）
- Windows トースト通知対応
- PyInstallerで単体exeにビルド可能

## セットアップ

```bash
pip install -r requirements.txt
```

## 使い方

### Pythonから直接実行

```bash
python screenshot_tool.py
```

### exeとしてビルド

```bash
python build.py
```

`dist/GameScreenshotTool.exe` が生成されます。ダブルクリックで起動できます。

## GUI画面

起動すると設定ウィンドウが開きます。

- **ショートカットキー**: 「変更」ボタンを押してキーを入力
- **保存先フォルダ**: 「参照」ボタンでフォルダを選択
- **JPG画質**: スライダーで調整 (1-100)
- **通知設定**: トースト通知 / 撮影音 のON/OFF
- **ゲーム検出**: プロセス名・ウィンドウタイトルの使用切替
- **エイリアス**: exe名 → 表示名のマッピングを追加・編集・削除

### 操作

1. 設定を調整
2. 「開始」ボタンで撮影待機開始
3. ゲーム中にショートカットキーを押すと撮影
4. 「トレイに格納」でシステムトレイに最小化

### システムトレイ

トレイアイコンを右クリックで：
- **撮影開始 / 撮影停止**: 撮影の切り替え
- **設定**: 設定ウィンドウを再表示
- **終了**: アプリケーションを終了

## 設定ファイル (config.json)

GUIから編集可能ですが、直接編集もできます。

| キー | 説明 | デフォルト |
|------|------|-----------|
| `hotkey` | 撮影ショートカットキー | `PrintScreen` |
| `save_directory` | 保存先ベースフォルダ | `~/Pictures/GameScreenshots` |
| `jpg_quality` | JPG画質 (1-100) | `95` |
| `notification` | トースト通知を表示 | `true` |
| `sound` | 撮影音を再生 | `false` |
| `timestamp_format` | タイムスタンプ形式 | `%Y%m%d_%H%M%S` |

### ゲーム名エイリアス

`game_detection.process_name_aliases` でexe名と表示名を対応付けできます。

```json
{
    "process_name_aliases": {
        "eldenring.exe": "Elden Ring",
        "GenshinImpact.exe": "Genshin Impact",
        "VALORANT-Win64-Shipping.exe": "VALORANT"
    }
}
```

## フォルダ構成例

```
~/Pictures/GameScreenshots/
├── Elden Ring/
│   ├── 20260311_153045.jpg
│   └── 20260311_160512.jpg
├── Genshin Impact/
│   └── 20260311_180023.jpg
└── Unknown/
    └── 20260311_120000.jpg
```

## ファイル構成

```
game-screenshot-tool/
├── screenshot_tool.py   # メインエントリーポイント
├── gui.py               # GUI設定画面
├── tray.py              # システムトレイ
├── game_detector.py     # ゲーム名検出
├── config.json          # 設定ファイル
├── build.py             # exeビルドスクリプト
├── requirements.txt     # 依存パッケージ
└── README.md
```

## 必要環境

- Windows 10/11
- Python 3.8+
