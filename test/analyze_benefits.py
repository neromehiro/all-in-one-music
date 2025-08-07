#!/usr/bin/env python3
"""
benefits.mp3をAll-In-Oneで完全解析するスクリプト
出力はtest/benefits_analysis/以下に保存
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# 親ディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

# matplotlibのバックエンドを非GUI版に設定
import matplotlib
matplotlib.use('Agg')

def analyze_benefits():
    """benefits.mp3の完全解析を実行"""
    
    print("🎵 benefits.mp3のAll-In-One音楽解析")
    print("=" * 60)
    print(f"📅 実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 分析対象ファイル
    audio_file = Path("module/sample_data/benefits.mp3")
    
    # ファイル存在確認
    if not audio_file.exists():
        print(f"❌ 音楽ファイルが見つかりません: {audio_file}")
        return False
    
    print(f"📁 分析対象: {audio_file}")
    print(f"📊 ファイルサイズ: {audio_file.stat().st_size / (1024*1024):.2f} MB")
    print()
    
    # 出力ディレクトリをtest以下に設定
    output_base_dir = Path("test/benefits_analysis")
    
    # サブディレクトリの設定
    results_dir = output_base_dir / "results"
    visualizations_dir = output_base_dir / "visualizations"
    sonifications_dir = output_base_dir / "sonifications"
    demix_dir = output_base_dir / "demix"
    spectrograms_dir = output_base_dir / "spectrograms"
    cache_dir = output_base_dir / "cache"
    
    # ディレクトリ作成
    for dir_path in [results_dir, visualizations_dir, sonifications_dir,
                    demix_dir, spectrograms_dir, cache_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    print("🔧 出力ディレクトリ構造:")
    print(f"  📂 {output_base_dir}")
    print(f"    ├── results/         # 分析結果")
    print(f"    ├── visualizations/  # PDF可視化")
    print(f"    ├── sonifications/   # ビート付き音声")
    print(f"    ├── demix/          # 音源分離")
    print(f"    ├── spectrograms/    # スペクトログラム")
    print(f"    └── cache/          # キャッシュ")
    print()
    
    try:
        # allin1ライブラリをインポート
        import allin1
        print("✅ allin1ライブラリのインポート成功")
        print()
        
        # 完全分析を実行（可視化・音響化含む）
        print("🎼 音楽分析を開始...")
        print("  - BPM・ビート検出")
        print("  - セクション分類")
        print("  - 音源分離（bass, drums, other, vocals）")
        print("  - 可視化PDF生成")
        print("  - 音響化（ビート付き音声）")
        print()
        
        result = allin1.analyze(
            str(audio_file),
            out_dir=str(results_dir),
            visualize=str(visualizations_dir),  # PDF可視化
            sonify=str(sonifications_dir),      # ビート付き音声
            demix_dir=str(demix_dir),          # 音源分離
            spec_dir=str(spectrograms_dir),    # スペクトログラム
            include_activations=True,
            include_embeddings=True,
            overwrite=True,
            multiprocess=False  # ハング回避
        )
        
        print("✅ 分析完了！")
        print()
        print("📊 分析結果サマリー:")
        print("=" * 40)
        print(f"🎼 BPM: {result.bpm:.1f}")
        print(f"🥁 ビート数: {len(result.beats)}")
        print(f"📍 ダウンビート数: {len(result.downbeats)}")
        print(f"🎯 セグメント数: {len(result.segments)}")
        
        # 総時間を計算
        total_duration = result.segments[-1].end if result.segments else 0
        print(f"⏱️ 総時間: {total_duration:.1f}秒")
        print()
        
        # セクション構造の表示
        print("🎵 楽曲構造:")
        print("-" * 40)
        for i, segment in enumerate(result.segments, 1):
            duration = segment.end - segment.start
            print(f"{i:2d}. {segment.start:6.1f}s - {segment.end:6.1f}s "
                  f"({duration:5.1f}s): {segment.label}")
        
        # セクション統計
        print()
        print("📈 セクション統計:")
        print("-" * 40)
        section_stats = {}
        for segment in result.segments:
            label = segment.label
            duration = segment.end - segment.start
            if label not in section_stats:
                section_stats[label] = {'count': 0, 'total_duration': 0}
            section_stats[label]['count'] += 1
            section_stats[label]['total_duration'] += duration
        
        for label, stats in section_stats.items():
            avg_duration = stats['total_duration'] / stats['count']
            print(f"  {label:10s}: {stats['count']:2d}回, "
                  f"合計{stats['total_duration']:6.1f}秒, "
                  f"平均{avg_duration:5.1f}秒")
        
        # 生成ファイルの確認
        print()
        print("💾 生成ファイル:")
        print("-" * 40)
        
        base_name = audio_file.stem
        files_to_check = [
            ("JSON結果", results_dir / f"{base_name}.json"),
            ("アクティベーション", results_dir / f"{base_name}.activ.npz"),
            ("エンベディング", results_dir / f"{base_name}.embed.npy"),
            ("可視化PDF", visualizations_dir / f"{base_name}.pdf"),
            ("音響化WAV", sonifications_dir / f"{base_name}.sonif.wav"),
            ("スペクトログラム", spectrograms_dir / f"{base_name}.npy"),
        ]
        
        for desc, filepath in files_to_check:
            if filepath.exists():
                size_mb = filepath.stat().st_size / (1024 * 1024)
                print(f"  ✅ {desc:15s}: {filepath.name} ({size_mb:.2f} MB)")
            else:
                print(f"  ⏳ {desc:15s}: 生成中または未生成")
        
        # 音源分離ファイルの確認
        demix_dir_path = demix_dir / "htdemucs" / base_name
        if demix_dir_path.exists():
            print()
            print("🎸 音源分離ファイル:")
            for stem_file in demix_dir_path.glob("*.wav"):
                size_mb = stem_file.stat().st_size / (1024 * 1024)
                print(f"  ✅ {stem_file.name:12s}: {size_mb:.2f} MB")
        
        # 分析結果を辞書形式で保存
        analysis_result = {
            "file_path": str(audio_file),
            "file_name": audio_file.name,
            "bpm": result.bpm,
            "beats": result.beats.tolist() if hasattr(result.beats, 'tolist') else result.beats,
            "downbeats": result.downbeats.tolist() if hasattr(result.downbeats, 'tolist') else result.downbeats,
            "beat_positions": result.beat_positions.tolist() if hasattr(result.beat_positions, 'tolist') else result.beat_positions,
            "segments": [
                {
                    "start": seg.start,
                    "end": seg.end,
                    "label": seg.label,
                    "duration": seg.end - seg.start
                }
                for seg in result.segments
            ],
            "total_duration": total_duration,
            "analysis_metadata": {
                "beat_count": len(result.beats),
                "downbeat_count": len(result.downbeats),
                "segment_count": len(result.segments),
                "analysis_date": datetime.now().isoformat()
            }
        }
        
        # 結果をJSONファイルに保存
        output_json = results_dir / f"{base_name}_full_analysis.json"
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        print()
        print(f"📝 完全分析結果を保存: {output_json}")
        
        print()
        print("🎉 benefits.mp3の解析が完了しました！")
        print()
        print("📍 次のステップ:")
        print(f"  1. PDF可視化を確認: {visualizations_dir / f'{base_name}.pdf'}")
        print(f"  2. ビート付き音声を確認: {sonifications_dir / f'{base_name}.sonif.wav'}")
        print(f"  3. 音源分離ファイルを確認: {demix_dir / 'htdemucs' / base_name}/")
        
        return True
        
    except ImportError as e:
        print(f"❌ ライブラリインポートエラー: {e}")
        print()
        print("📦 必要なライブラリをインストールしてください:")
        print("  pip install allin1")
        print("  pip install torch torchaudio")
        print("  pip install git+https://github.com/CPJKU/madmom")
        return False
        
    except Exception as e:
        print(f"❌ 分析エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン実行関数"""
    success = analyze_benefits()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
