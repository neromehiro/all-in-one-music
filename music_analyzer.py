#!/usr/bin/env python3
"""
All-In-One音楽分析機能をmain.pyに統合するためのモジュール
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Union
import logging

# matplotlibのバックエンドを非GUI版に設定
import matplotlib
matplotlib.use('Agg')

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MusicAnalyzer:
    """音楽分析クラス"""
    
    def __init__(self, output_dir: str = "analysis_results"):
        """
        初期化
        
        Args:
            output_dir: 分析結果の出力ディレクトリ
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # allin1ライブラリの遅延インポート
        self._allin1 = None
    
    @property
    def allin1(self):
        """allin1ライブラリの遅延インポート"""
        if self._allin1 is None:
            try:
                import allin1
                self._allin1 = allin1
                logger.info("allin1ライブラリのインポート成功")
            except ImportError as e:
                logger.error(f"allin1ライブラリのインポートに失敗: {e}")
                raise
        return self._allin1
    
    def analyze_audio_file(
        self,
        audio_file_path: Union[str, Path],
        include_visualization: bool = False,
        include_sonification: bool = False,
        overwrite: bool = False
    ) -> Optional[Dict]:
        """
        音楽ファイルを分析
        
        Args:
            audio_file_path: 分析対象の音楽ファイルパス
            include_visualization: 可視化を含めるか
            include_sonification: 音響化を含めるか
            overwrite: 既存結果を上書きするか
            
        Returns:
            分析結果の辞書、失敗時はNone
        """
        audio_path = Path(audio_file_path)
        
        if not audio_path.exists():
            logger.error(f"音楽ファイルが見つかりません: {audio_path}")
            return None
        
        logger.info(f"音楽分析開始: {audio_path.name}")
        
        try:
            # 出力設定
            viz_dir = self.output_dir / "visualizations" if include_visualization else None
            sonif_dir = self.output_dir / "sonifications" if include_sonification else None
            
            if viz_dir:
                viz_dir.mkdir(parents=True, exist_ok=True)
            if sonif_dir:
                sonif_dir.mkdir(parents=True, exist_ok=True)
            
            # 分析実行
            result = self.allin1.analyze(
                str(audio_path),
                out_dir=str(self.output_dir),
                visualize=str(viz_dir) if include_visualization else False,
                sonify=str(sonif_dir) if include_sonification else False,
                include_activations=True,
                include_embeddings=True,
                overwrite=overwrite,
                multiprocess=False  # ハング回避
            )
            
            # 結果を辞書形式に変換
            analysis_result = {
                "file_path": str(audio_path),
                "file_name": audio_path.name,
                "bpm": result.bpm,
                "beats": result.beats,
                "downbeats": result.downbeats,
                "beat_positions": result.beat_positions,
                "segments": [
                    {
                        "start": seg.start,
                        "end": seg.end,
                        "label": seg.label,
                        "duration": seg.end - seg.start
                    }
                    for seg in result.segments
                ],
                "total_duration": result.segments[-1].end if result.segments else 0,
                "analysis_metadata": {
                    "beat_count": len(result.beats),
                    "downbeat_count": len(result.downbeats),
                    "segment_count": len(result.segments),
                    "has_activations": hasattr(result, 'activations') and result.activations is not None,
                    "has_embeddings": hasattr(result, 'embeddings') and result.embeddings is not None
                }
            }
            
            logger.info(f"分析完了: BPM={result.bpm}, セグメント数={len(result.segments)}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"分析エラー: {e}")
            return None
    
    def load_analysis_result(self, json_file_path: Union[str, Path]) -> Optional[Dict]:
        """
        保存された分析結果を読み込み
        
        Args:
            json_file_path: JSONファイルのパス
            
        Returns:
            分析結果の辞書、失敗時はNone
        """
        json_path = Path(json_file_path)
        
        if not json_path.exists():
            logger.error(f"分析結果ファイルが見つかりません: {json_path}")
            return None
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"分析結果読み込み成功: {json_path.name}")
            return data
            
        except Exception as e:
            logger.error(f"分析結果読み込みエラー: {e}")
            return None
    
    def get_music_structure_summary(self, analysis_result: Dict) -> Dict:
        """
        楽曲構造のサマリーを取得
        
        Args:
            analysis_result: 分析結果の辞書
            
        Returns:
            構造サマリーの辞書
        """
        if not analysis_result or 'segments' not in analysis_result:
            return {}
        
        segments = analysis_result['segments']
        
        # セクション統計
        section_stats = {}
        for segment in segments:
            label = segment['label']
            duration = segment.get('duration', segment['end'] - segment['start'])
            
            if label not in section_stats:
                section_stats[label] = {
                    'count': 0,
                    'total_duration': 0,
                    'durations': []
                }
            
            section_stats[label]['count'] += 1
            section_stats[label]['total_duration'] += duration
            section_stats[label]['durations'].append(duration)
        
        # 平均時間を計算
        for label, stats in section_stats.items():
            stats['average_duration'] = stats['total_duration'] / stats['count']
        
        return {
            'total_duration': analysis_result.get('total_duration', 0),
            'bpm': analysis_result.get('bpm', 0),
            'segment_count': len(segments),
            'section_stats': section_stats,
            'structure_sequence': [seg['label'] for seg in segments]
        }
    
    def batch_analyze(
        self,
        audio_files: List[Union[str, Path]],
        include_visualization: bool = False,
        include_sonification: bool = False
    ) -> List[Dict]:
        """
        複数の音楽ファイルを一括分析
        
        Args:
            audio_files: 分析対象の音楽ファイルリスト
            include_visualization: 可視化を含めるか
            include_sonification: 音響化を含めるか
            
        Returns:
            分析結果のリスト
        """
        results = []
        
        for audio_file in audio_files:
            logger.info(f"一括分析 ({len(results)+1}/{len(audio_files)}): {Path(audio_file).name}")
            
            result = self.analyze_audio_file(
                audio_file,
                include_visualization=include_visualization,
                include_sonification=include_sonification
            )
            
            if result:
                results.append(result)
            else:
                logger.warning(f"分析失敗: {audio_file}")
        
        logger.info(f"一括分析完了: {len(results)}/{len(audio_files)} 成功")
        return results

def main():
    """テスト実行"""
    print("🎵 音楽分析モジュールテスト")
    print("=" * 40)
    
    # 分析器の初期化
    analyzer = MusicAnalyzer("test/analysis_results")
    
    # サンプルファイルの分析
    sample_file = "module/sample_data/1-03 Additional Memory.m4a"
    
    if Path(sample_file).exists():
        print(f"📁 分析対象: {Path(sample_file).name}")
        
        # 既存結果の読み込みテスト
        json_file = "test/analysis_results/1-03 Additional Memory.json"
        if Path(json_file).exists():
            result = analyzer.load_analysis_result(json_file)
            if result:
                print("✅ 既存結果読み込み成功")
                
                # 構造サマリーの取得
                summary = analyzer.get_music_structure_summary(result)
                print(f"📊 BPM: {summary['bpm']}")
                print(f"⏱️  総時間: {summary['total_duration']:.1f}秒")
                print(f"🎯 セグメント数: {summary['segment_count']}")
                
                print("\n🎼 セクション統計:")
                for label, stats in summary['section_stats'].items():
                    print(f"  {label}: {stats['count']}回, 平均{stats['average_duration']:.1f}秒")
            else:
                print("❌ 既存結果読み込み失敗")
        else:
            print("📊 新規分析を実行...")
            result = analyzer.analyze_audio_file(sample_file)
            if result:
                print("✅ 新規分析成功")
            else:
                print("❌ 新規分析失敗")
    else:
        print(f"❌ サンプルファイルが見つかりません: {sample_file}")
    
    print("\n🎉 音楽分析モジュールテスト完了")

if __name__ == "__main__":
    main()
