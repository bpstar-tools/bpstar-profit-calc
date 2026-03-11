# Game Screenshot Tool

Windows向けゲームスクリーンショットツール。ショートカットキーでアクティブモニターを撮影し、ゲームごとに自動フォルダ分けします。

## 機能

- ショートカットキーでスクリーンショット撮影（設定変更可能）
- アクティブウィンドウが表示されているモニターのみを撮影
- ゲーム名を自動検出してフォルダ分け（プロセス名 + ウィンドウタイトル）
- JPG形式で保存（画質設定可能）
- ファイル名はタイムスタンプ
- Windows トースト通知対応

## セットアップ

```bash
pip install -r requirements.txt
```

## 使い方

```bash
python screenshot_tool.py
```

起動後、設定したホットキー（デフォルト: PrintScreen）を押すとスクリーンショットが撮影されます。
終了は `Ctrl+C` です。

## 設定 (config.json)

| キー | 説明 | デフォルト |
|------|------|-----------|
| `hotkey` | 撮影ショートカットキー | `PrintScreen` |
| `save_directory` | 保存先ベースフォルダ | `~/Pictures/GameScreenshots` |
| `jpg_quality` | JPG画質 (1-100) | `95` |
| `notification` | トースト通知を表示 | `true` |
| `sound` | 撮影音を再生 | `false` |
| `timestamp_format` | ファイル名のタイムスタンプ形式 | `%Y%m%d_%H%M%S` |

### ゲーム検出設定 (game_detection)

| キー | 説明 |
|------|------|
| `use_process_name` | プロセス名でゲームを検出 |
| `use_window_title` | ウィンドウタイトルでゲームを検出 |
| `process_name_aliases` | プロセス名→表示名のマッピング |
| `title_cleanup_patterns` | タイトルからノイズを除去する正規表現パターン |

#### エイリアス例

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

## 必要環境

- Windows 10/11
- Python 3.8+
