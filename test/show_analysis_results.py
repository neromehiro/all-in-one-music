#!/usr/bin/env python3
"""
All-In-One音楽分析結果の表示スクリプト
生成された分析結果を見やすく表示する
"""

import json
import numpy as np
from pathlib import Path

def format_time(seconds):
    """秒を分:秒形式に変換"""
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}:{secs:05.2f}"

def show_analysis_results():
    """分析結果の表示"""
    print("🎵 All-In-One音楽分析結果")
    print("=" * 60)
    
    # JSONファイルの読み込み（新しいディレクトリ構造）
    json_file = Path("music_analysis/results/1-03 Additional Memory.json")
    
    if not json_file.exists():
        print("❌ 分析結果ファイルが見つかりません")
        return False
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 基本情報の表示
    print(f"📁 ファイル: {Path(data['path']).name}")
    print(f"🎼 BPM: {data['bpm']}")
    print(f"⏱️  総再生時間: {format_time(data['segments'][-1]['end'])}")
    print(f"🥁 ビート数: {len(data['beats'])}")
    print(f"📊 ダウンビート数: {len(data['downbeats'])}")
    print(f"🎯 セグメント数: {len(data['segments'])}")
    
    # セグメント詳細の表示
    print("\n🎼 楽曲構造分析:")
    print("-" * 60)
    print(f"{'No.':<3} {'開始時間':<10} {'終了時間':<10} {'長さ':<8} {'セクション':<10}")
    print("-" * 60)
    
    total_duration = 0
    for i, segment in enumerate(data['segments']):
        start_time = format_time(segment['start'])
        end_time = format_time(segment['end'])
        duration = segment['end'] - segment['start']
        total_duration += duration
        duration_str = format_time(duration)
        
        print(f"{i+1:<3} {start_time:<10} {end_time:<10} {duration_str:<8} {segment['label']:<10}")
    
    print("-" * 60)
    print(f"合計時間: {format_time(total_duration)}")
    
    # セクション統計
    print("\n📈 セクション統計:")
    print("-" * 30)
    section_stats = {}
    for segment in data['segments']:
        label = segment['label']
        duration = segment['end'] - segment['start']
        if label not in section_stats:
            section_stats[label] = {'count': 0, 'total_duration': 0}
        section_stats[label]['count'] += 1
        section_stats[label]['total_duration'] += duration
    
    for label, stats in section_stats.items():
        avg_duration = stats['total_duration'] / stats['count']
        print(f"{label:<10}: {stats['count']}回, 平均{format_time(avg_duration)}, 合計{format_time(stats['total_duration'])}")
    
    # ファイル情報
    print("\n📂 生成されたファイル:")
    print("-" * 30)
    
    files_to_check = [
        ("分析結果JSON", "music_analysis/results/1-03 Additional Memory.json"),
        ("アクティベーション", "music_analysis/results/1-03 Additional Memory.activ.npz"),
        ("エンベディング", "music_analysis/results/1-03 Additional Memory.embed.npy"),
        ("可視化PDF", "music_analysis/visualizations/1-03 Additional Memory.pdf"),
        ("音源分離(Bass)", "music_analysis/demix/htdemucs/1-03 Additional Memory/bass.wav"),
        ("音源分離(Drums)", "music_analysis/demix/htdemucs/1-03 Additional Memory/drums.wav"),
        ("音源分離(Other)", "music_analysis/demix/htdemucs/1-03 Additional Memory/other.wav"),
        ("音源分離(Vocals)", "music_analysis/demix/htdemucs/1-03 Additional Memory/vocals.wav"),
        ("スペクトログラム", "music_analysis/spectrograms/1-03 Additional Memory.npy"),
    ]
    
    for desc, filepath in files_to_check:
        path = Path(filepath)
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            print(f"✅ {desc:<15}: {size_mb:.1f} MB")
        else:
            print(f"❌ {desc:<15}: ファイルなし")
    
    # アクティベーションデータの確認
    activ_file = Path("music_analysis/results/1-03 Additional Memory.activ.npz")
    if activ_file.exists():
        print("\n🔬 アクティベーションデータ:")
        print("-" * 30)
        activ_data = np.load(activ_file)
        for key in activ_data.files:
            shape = activ_data[key].shape
            print(f"{key:<12}: {shape}")
    
    # エンベディングデータの確認
    embed_file = Path("music_analysis/results/1-03 Additional Memory.embed.npy")
    if embed_file.exists():
        print("\n🧠 エンベディングデータ:")
        print("-" * 30)
        embed_data = np.load(embed_file)
        print(f"形状: {embed_data.shape}")
        print(f"サイズ: {embed_data.nbytes / (1024*1024):.1f} MB")
    
    return True

def main():
    """メイン実行関数"""
    success = show_analysis_results()
    
    if success:
        print("\n🎉 分析結果の表示が完了しました！")
        print("\n💡 次のステップ:")
        print("  - PDFファイルを開いて可視化結果を確認")
        print("  - 音源分離されたWAVファイルを再生")
        print("  - 分析結果をアプリケーションに統合")
    else:
        print("\n❌ 分析結果の表示に失敗しました")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
