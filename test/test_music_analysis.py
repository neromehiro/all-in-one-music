#!/usr/bin/env python3
"""
All-In-One音楽分析の実行テストスクリプト
サンプル音楽ファイルを使用して実際の分析を行う
"""

import os
import sys
import json
from pathlib import Path

def test_allin1_analysis():
    """All-In-One音楽分析のテスト実行"""
    print("🎵 All-In-One音楽分析テスト開始")
    print("=" * 50)
    
    # サンプル音楽ファイルのパス
    sample_file = Path("module/sample_data/1-03 Additional Memory.m4a")
    
    if not sample_file.exists():
        print(f"❌ サンプルファイルが見つかりません: {sample_file}")
        return False
    
    print(f"📁 分析対象ファイル: {sample_file}")
    
    try:
        # allin1ライブラリをインポート
        import allin1
        print("✅ allin1ライブラリのインポートに成功")
        
        # 出力ディレクトリの設定
        output_dir = Path("test/analysis_results")
        viz_dir = Path("test/visualizations")
        sonif_dir = Path("test/sonifications")
        
        # ディレクトリを作成
        output_dir.mkdir(exist_ok=True)
        viz_dir.mkdir(exist_ok=True)
        sonif_dir.mkdir(exist_ok=True)
        
        print("📊 音楽分析を開始...")
        
        # 基本分析の実行
        result = allin1.analyze(
            str(sample_file),
            out_dir=str(output_dir),
            visualize=str(viz_dir),
            sonify=str(sonif_dir),
            include_activations=True,
            include_embeddings=True
        )
        
        print("✅ 分析が完了しました！")
        
        # 結果の表示
        print("\n📈 分析結果:")
        print(f"  - BPM: {result.bpm}")
        print(f"  - ビート数: {len(result.beats)}")
        print(f"  - ダウンビート数: {len(result.downbeats)}")
        print(f"  - セグメント数: {len(result.segments)}")
        
        print("\n🎼 セグメント詳細:")
        for i, segment in enumerate(result.segments[:10]):  # 最初の10セグメントのみ表示
            print(f"  {i+1:2d}. {segment.start:6.2f}s - {segment.end:6.2f}s: {segment.label}")
        
        if len(result.segments) > 10:
            print(f"  ... (他 {len(result.segments) - 10} セグメント)")
        
        # 結果をJSONファイルに保存
        json_output = output_dir / f"{sample_file.stem}_analysis.json"
        analysis_data = {
            "file": str(sample_file),
            "bpm": result.bpm,
            "beats": result.beats,
            "downbeats": result.downbeats,
            "beat_positions": result.beat_positions,
            "segments": [
                {
                    "start": seg.start,
                    "end": seg.end,
                    "label": seg.label
                }
                for seg in result.segments
            ]
        }
        
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 分析結果をJSONファイルに保存: {json_output}")
        
        # ファイルサイズの確認
        if json_output.exists():
            size_kb = json_output.stat().st_size / 1024
            print(f"  - ファイルサイズ: {size_kb:.1f} KB")
        
        return True
        
    except ImportError as e:
        print(f"❌ ライブラリのインポートエラー: {e}")
        print("💡 先に test_allin1_dependencies.py を実行してください")
        return False
    except Exception as e:
        print(f"❌ 分析中にエラーが発生しました: {e}")
        return False

def main():
    """メイン実行関数"""
    success = test_allin1_analysis()
    
    if success:
        print("\n🎉 音楽分析テストが正常に完了しました！")
        print("\n📂 生成されたファイル:")
        print("  - test/analysis_results/: 分析結果JSON")
        print("  - test/visualizations/: 可視化画像")
        print("  - test/sonifications/: 音響化音声")
    else:
        print("\n❌ 音楽分析テストに失敗しました")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
