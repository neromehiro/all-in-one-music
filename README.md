cd ui/music-dissector && npm run dev

# All-In-One Music Analysis

🎵 All-In-One音楽構造解析ライブラリを統合した音楽分析システム

## 📋 概要

このプロジェクトは、[mir-aidj/all-in-one](https://github.com/mir-aidj/all-in-one)ライブラリを統合し、音楽ファイルの包括的な分析を行うシステムです。

### 🎯 主な機能

- **音楽構造解析**: テンポ（BPM）、ビート、ダウンビートの自動検出
- **セクション分類**: intro, verse, chorus, bridge, outro等の自動ラベリング
- **音源分離**: HTDemucsによる4チャンネル分離（bass, drums, other, vocals）
- **可視化**: 楽曲構造の視覚的表示（PDF出力）
- **音響化**: ビート・セグメント境界のクリック音付き音声生成

## 🚀 セットアップ

### 1. 依存関係のインストール

```bash
# 依存関係の自動チェック・インストール
python test/test_allin1_dependencies.py
```

### 2. 手動インストール（必要に応じて）

```bash
# PyTorchのインストール（システムに応じて）
pip install torch torchaudio

# madmomの最新版インストール
pip install git+https://github.com/CPJKU/madmom

# All-In-Oneライブラリのインストール
pip install allin1

# FFmpeg（MP3サポート用、macOS）
brew install ffmpeg
```

## 📁 出力ディレクトリ構造

分析結果は`music_analysis/`フォルダ以下に整理されて保存されます：

```
music_analysis/
├── results/         # 分析結果ファイル
│   ├── *.json      # 分析結果（BPM、ビート、セグメント等）
│   ├── *.activ.npz # アクティベーションデータ（ビート・セグメント検出）
│   └── *.embed.npy # エンベディングデータ（高次元特徴量）
├── visualizations/  # 可視化ファイル
│   └── *.pdf       # 楽曲構造の視覚的表示
├── sonifications/   # 音響化ファイル
│   └── *.sonif.wav # ビート・セグメント境界付き音声
├── demix/          # 音源分離ファイル
│   └── htdemucs/   # HTDemucsによる分離結果
│       └── [曲名]/
│           ├── bass.wav    # ベース音源
│           ├── drums.wav   # ドラム音源
│           ├── other.wav   # その他音源
│           └── vocals.wav  # ボーカル音源
├── spectrograms/    # スペクトログラムデータ
│   └── *.npy       # 周波数解析データ
└── cache/          # 一時ファイル
```

## 🎵 使用方法

### 基本的な分析

```python
from music_analyzer import MusicAnalyzer

# 分析器の初期化
analyzer = MusicAnalyzer("music_analysis")

# 音楽ファイルの分析
result = analyzer.analyze_audio_file("your_music.mp3")

# 結果の表示
print(f"BPM: {result['bpm']}")
print(f"セグメント数: {len(result['segments'])}")
```

### 可視化・音響化付き分析

```python
# 可視化・音響化を含む分析
result = analyzer.analyze_audio_file(
    "your_music.mp3",
    include_visualization=True,  # PDF可視化
    include_sonification=True    # 音響化
)
```

### 複数ファイルの一括分析

```python
# 複数ファイルの一括処理
audio_files = ["song1.mp3", "song2.wav", "song3.m4a"]
results = analyzer.batch_analyze(audio_files)
```

## 🛠️ コマンドラインツール

### 1. 依存関係チェック

```bash
python test/test_allin1_dependencies.py
```

### 2. 軽量版分析（推奨）

```bash
python test/simple_music_analysis.py
```

### 3. フル機能分析

```bash
python test/test_music_analysis.py
```

### 4. 分析結果表示

```bash
python test/show_analysis_results.py
```

### 5. 音楽分析モジュールテスト

```bash
python music_analyzer.py
```

## 📊 分析結果の例

### JSON出力例

```json
{
  "file_name": "song.mp3",
  "bpm": 120,
  "beats": [0.5, 1.0, 1.5, 2.0, ...],
  "downbeats": [0.5, 2.5, 4.5, ...],
  "segments": [
    {
      "start": 0.0,
      "end": 8.0,
      "label": "intro",
      "duration": 8.0
    },
    {
      "start": 8.0,
      "end": 32.0,
      "label": "verse",
      "duration": 24.0
    }
  ],
  "total_duration": 240.5
}
```

### セクションラベル

- `start`: 楽曲開始
- `intro`: イントロ
- `verse`: バース
- `chorus`: コーラス
- `bridge`: ブリッジ
- `inst`: インストゥルメンタル
- `solo`: ソロ
- `outro`: アウトロ
- `end`: 楽曲終了

## 🔧 トラブルシューティング

### matplotlibハング問題

可視化処理で停止する場合：

```bash
# 環境変数でバックエンドを指定
MPLBACKEND=Agg python your_script.py
```

### メモリ不足

大きなファイルの分析時：

```python
# マルチプロセシングを無効化
result = analyzer.analyze_audio_file(
    "large_file.mp3",
    multiprocess=False
)
```

### MP3ファイルの問題

MP3ファイルは事前にWAVに変換することを推奨：

```bash
ffmpeg -i input.mp3 output.wav
```

## 📈 パフォーマンス

- **RTX 4090 + Intel i9-10940X**: 10曲（33分）を73秒で処理
- **ファイルサイズ**: 4分の楽曲で約200MB（全データ含む）
- **メモリ使用量**: 分析時に約2-4GB

## 🔗 関連リンク

- [All-In-One GitHub](https://github.com/mir-aidj/all-in-one)
- [All-In-One Paper](http://arxiv.org/abs/2307.16425)
- [Hugging Face Demo](https://huggingface.co/spaces/taejunkim/all-in-one/)

## 📝 ライセンス

このプロジェクトは、統合されたライブラリのライセンスに従います。

## 🤝 貢献

バグ報告や機能要望は、GitHubのIssuesでお知らせください。

---

**注意**: 初回実行時は、モデルのダウンロードに時間がかかる場合があります。
