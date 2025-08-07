#!/usr/bin/env python3
"""
All-In-One音楽分析の軽量版テストスクリプト
matplotlibバックエンド問題を解決し、可視化・音響化を制御可能にした版
"""

import os
import sys
import json
import numpy as np
from pathlib import Path

# matplotlibのバックエンドを非GUI版に設定（重要！）
import matplotlib
matplotlib.use('Agg')  # GUIを使わないバックエンドに設定

def simple_allin1_analysis(
    audio_file_path,
    enable_visualization=False,
    enable_sonification=False,
    output_base_dir="test"
):
    """
    All-In-One音楽分析の軽量実行
    
    Args:
        audio_file_path: 分析対象の音楽ファイルパス
        enable_visualization: 可視化を有効にするか
        enable_sonification: 音響化を有効にするか
        output_base_dir: 出力ベースディレクトリ
    """
    print("🎵 All-In-One軽量音楽分析開始")
    print("=" * 50)
    
    # ファイル存在確認
    audio_path = Path(audio_file_path)
    if not audio_path.exists():
        print(f"❌ 音楽ファイルが見つかりません: {audio_path}")
        return False
    
    print(f"📁 分析対象: {audio_path.name}")
    print(f"📊 可視化: {'有効' if enable_visualization else '無効'}")
    print(f"🔊 音響化: {'有効' if enable_sonification else '無効'}")
    
    try:
        # allin1ライブラリをインポート
        import allin1
        print("✅ allin1ライブラリのインポート成功")
        
        # 出力ディレクトリの設定
        output_dir = Path(output_base_dir) / "analysis_results"
        viz_dir = Path(output_base_dir) / "visualizations" if enable_visualization else None
        sonif_dir = Path(output_base_dir) / "sonifications" if enable_sonification else None
        
        # ディレクトリ作成
        output_dir.mkdir(parents=True, exist_ok=True)
        if viz_dir:
            viz_dir.mkdir(parents=True, exist_ok=True)
        if sonif_dir:
            sonif_dir.mkdir(parents=True, exist_ok=True)
        
        print("📊 音楽分析を実行中...")
        
        # 分析実行（可視化・音響化は条件付き）
        result = allin1.analyze(
            str(audio_path),
            out_dir=str(output_dir),
            visualize=str(viz_dir) if enable_visualization else False,
            sonify=str(sonif_dir) if enable_sonification else False,
            include_activations=True,
            include_embeddings=True,
            multiprocess=False  # マルチプロセシングを無効化してハング回避
        )
        
        print("✅ 分析完了！")
        
        # 結果の表示
        print("\n📈 分析結果サマリー:")
        print(f"  🎼 BPM: {result.bpm}")
        print(f"  🥁 ビート数: {len(result.beats)}")
        print(f"  📊 ダウンビート数: {len(result.downbeats)}")
        print(f"  🎯 セグメント数: {len(result.segments)}")
        
        # 楽曲構造の表示
        print("\n🎼 楽曲構造:")
        for i, segment in enumerate(result.segments[:8]):  # 最初の8セグメントのみ
            duration = segment.end - segment.start
            print(f"  {i+1:2d}. {segment.start:6.1f}s-{segment.end:6.1f}s ({duration:5.1f}s): {segment.label}")
        
        if len(result.segments) > 8:
            print(f"  ... (他 {len(result.segments) - 8} セグメント)")
        
        # ファイル保存確認
        json_file = output_dir / f"{audio_path.stem}.json"
        if json_file.exists():
            size_kb = json_file.stat().st_size / 1024
            print(f"\n💾 結果保存: {json_file} ({size_kb:.1f} KB)")
        
        return True
        
    except ImportError as e:
        print(f"❌ ライブラリインポートエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ 分析エラー: {e}")
        return False

def show_existing_results():
    """既存の分析結果を表示"""
    print("\n🔍 既存の分析結果確認")
    print("-" * 30)
    
    results_dir = Path("test/analysis_results")
    if not results_dir.exists():
        print("❌ 分析結果ディレクトリが見つかりません")
        return
    
    json_files = list(results_dir.glob("*.json"))
    if not json_files:
        print("❌ 分析結果ファイルが見つかりません")
        return
    
    for json_file in json_files:
        print(f"\n📄 {json_file.name}:")
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"  BPM: {data['bpm']}")
            print(f"  セグメント数: {len(data['segments'])}")
            print(f"  総時間: {data['segments'][-1]['end']:.1f}秒")
            
            # セクション統計
            section_counts = {}
            for segment in data['segments']:
                label = segment['label']
                section_counts[label] = section_counts.get(label, 0) + 1
            
            print(f"  構造: {', '.join([f'{k}×{v}' for k, v in section_counts.items()])}")
            
        except Exception as e:
            print(f"  ❌ 読み込みエラー: {e}")

def main():
    """メイン実行関数"""
    print("🎵 All-In-One軽量音楽分析ツール")
    print("=" * 50)
    
    # 既存結果の確認
    show_existing_results()
    
    # サンプルファイルで新規分析（基本分析のみ）
    sample_file = "module/sample_data/1-03 Additional Memory.m4a"
    
    print(f"\n🚀 新規分析テスト（基本分析のみ）")
    success = simple_allin1_analysis(
        sample_file,
        enable_visualization=False,  # 可視化無効
        enable_sonification=False    # 音響化無効
    )
    
    if success:
        print("\n🎉 軽量分析テスト成功！")
        print("\n💡 次のステップ:")
        print("  - 可視化を有効にしたい場合: enable_visualization=True")
        print("  - 音響化を有効にしたい場合: enable_sonification=True")
        print("  - 既存のPDFファイルを確認: test/visualizations/")
    else:
        print("\n❌ 軽量分析テスト失敗")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
