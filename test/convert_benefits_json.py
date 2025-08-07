#!/usr/bin/env python3
"""
benefits.jsonをUI用の形式に変換するスクリプト
"""

import json
import numpy as np
from pathlib import Path
import sys

def convert_segments_format(segments):
    """セグメントデータを正しい形式に変換"""
    if not segments:
        return []
    
    # 辞書形式の場合、startの値だけを取り出す
    if isinstance(segments[0], dict):
        return [seg['start'] for seg in segments]
    # 2次元配列の場合
    elif isinstance(segments[0], list):
        return [seg[0] for seg in segments]
    # すでに1次元配列の場合
    return segments

def generate_dummy_frequency_bands(num_frames=5000):
    """ダミーの周波数帯域データを生成"""
    # ランダムな波形データを生成
    np.random.seed(42)
    base_wave = np.sin(np.linspace(0, 100, num_frames)) * 127 + 128
    noise = np.random.normal(0, 10, num_frames)
    
    low = np.clip(base_wave + noise * 0.5, 0, 255).astype(int).tolist()
    mid = np.clip(base_wave + noise * 1.0, 0, 255).astype(int).tolist()
    high = np.clip(base_wave + noise * 0.3, 0, 255).astype(int).tolist()
    
    return {"low": low, "mid": mid, "high": high}

def convert_benefits_json(input_path, output_path):
    """benefits.jsonをUI形式に変換"""
    
    print(f"📁 入力ファイル: {input_path}")
    
    # JSONファイルを読み込み
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 新しい形式のデータを作成
    converted = {
        "id": "benefits",
        "duration": data.get("total_duration", 246.2),
        "inferences": {
            "beats": data.get("beats", []),
            "downbeats": data.get("downbeats", []),
            "segments": convert_segments_format(data.get("segments", []))
        },
        "truths": {
            "beats": data.get("beats", [])[:2],  # 最初の2つだけ（ダミー）
            "segments": convert_segments_format(data.get("segments", []))
        },
        "scores": {
            "beat": {
                "f1": 0.95,
                "precision": 0.95,
                "recall": 0.95,
                "amlt": 0.95,
                "cmlt": 0.95
            },
            "downbeat": {
                "f1": 0.90,
                "precision": 0.90,
                "recall": 0.90,
                "amlt": 0.90,
                "cmlt": 0.90
            },
            "segment": {
                "F-measure@0.5": 0.85,
                "F-measure@3.0": 0.80,
                "Precision@0.5": 0.85,
                "Precision@3.0": 0.80,
                "Recall@0.5": 0.85,
                "Recall@3.0": 0.80,
                "Pairwise Precision": 0.75,
                "Pairwise Recall": 0.85,
                "Rand Index": 0.70,
                "Adjusted Rand Index": 0.65,
                "Mutual Information": 0.60,
                "Adjusted Mutual Information": 0.55,
                "Normalized Mutual Information": 0.65,
                "V-measure": 0.60,
                "V Precision": 0.65,
                "V Recall": 0.55,
                "NCE F-measure": 0.70,
                "NCE Over": 0.75,
                "NCE Under": 0.65,
                "Accuracy": 0.70,
                "Est-to-ref deviation": 0.05,
                "Ref-to-est deviation": 0.05
            }
        },
        "wav": {
            "drum": generate_dummy_frequency_bands(5000),
            "bass": generate_dummy_frequency_bands(5000),
            "vocal": generate_dummy_frequency_bands(5000),
            "other": generate_dummy_frequency_bands(5000)
        },
        "nav": {
            "drum": generate_dummy_frequency_bands(1000),
            "bass": generate_dummy_frequency_bands(1000),
            "vocal": generate_dummy_frequency_bands(1000),
            "other": generate_dummy_frequency_bands(1000)
        }
    }
    
    # 保存
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(converted, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 変換完了: {output_path}")
    
    # 構造の確認
    print("\n📊 変換後の構造:")
    print(f"  - duration: {converted['duration']:.1f}秒")
    print(f"  - beats: {len(converted['inferences']['beats'])}個")
    print(f"  - downbeats: {len(converted['inferences']['downbeats'])}個")
    print(f"  - segments: {len(converted['inferences']['segments'])}個")
    print(f"  - wav.drum.low: {len(converted['wav']['drum']['low'])}サンプル")
    print(f"  - nav.bass.mid: {len(converted['nav']['bass']['mid'])}サンプル")
    
    return converted

def main():
    print("=" * 60)
    print("🎵 benefits.json変換ツール")
    print("=" * 60)
    print()
    
    # 入力と出力のパス
    input_json = Path("test/benefits_analysis/results/benefits.json")
    output_json = Path("test/benefits_analysis/results/benefits_converted.json")
    
    if not input_json.exists():
        print(f"❌ 入力ファイルが見つかりません: {input_json}")
        return 1
    
    # 変換実行
    try:
        converted_data = convert_benefits_json(input_json, output_json)
        
        # 比較用にtest/compare_json_structure.pyで確認できるようにする
        print(f"\n📝 変換されたファイルを確認するには:")
        print(f"  python test/compare_json_structure.py")
        print(f"  対象ファイル: {output_json}")
        
        return 0
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
