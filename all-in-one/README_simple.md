# シンプル音楽分析ツール

音声ファイルから分析結果（JSON）と音源分離（Stem）を出力するシンプルなツールです。

## 🚀 セットアップ

```bash
# 必要なライブラリをインストール
pip install allin1
pip install torch torchaudio
pip install git+https://github.com/CPJKU/madmom
```

## 📊 使い方

### 単一ファイルの分析

```bash
python simple_analyzer.py "module/sample_data/1-03 Additional Memory.m4a"
```

### 複数ファイルの一括分析

```bash
python simple_analyzer.py file1.mp3 file2.wav file3.m4a
```

### 出力ディレクトリを指定

```bash
python simple_analyzer.py -o my_output audio.mp3
```

## 📁 出力構造

```
output/
└── [曲名]/
    ├── [曲名].json         # 分析結果
    └── stems/
        ├── bass.wav        # ベース
        ├── drums.wav       # ドラム
        ├── other.wav       # その他
        └── vocals.wav      # ボーカル
```

## 📋 JSON出力例

```json
{
  "file_name": "song.mp3",
  "file_path": "/path/to/song.mp3",
  "bpm": 120,
  "beats": [0.5, 1.0, 1.5, 2.0, ...],
  "downbeats": [0.5, 2.5, 4.5, ...],
  "beat_positions": [1, 2, 3, 4, 1, 2, 3, 4, ...],
  "segments": [
    {
      "start": 0.0,
      "end": 8.0,
      "label": "intro"
    },
    {
      "start": 8.0,
      "end": 32.0,
      "label": "verse"
    }
  ]
}
```

## 🎯 Pythonから使用

```python
from simple_analyzer import SimpleAnalyzer

# 分析器を初期化
analyzer = SimpleAnalyzer("output")

# 単一ファイルを分析
result = analyzer.analyze("song.mp3")

# 複数ファイルを一括分析
results = analyzer.batch_analyze(["song1.mp3", "song2.wav"])
```

## ⚡ 注意事項

- 初回実行時はモデルのダウンロードに時間がかかります
- GPUがない場合はCPUで実行されます（処理が遅くなります）
- MP3ファイルは事前にWAVに変換することを推奨
