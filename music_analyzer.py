#!/usr/bin/env python3
"""
All-In-One音楽分析機能をmain.pyに統合するためのモジュール
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Union
import logging
import shutil
import os

# matplotlibのバックエンドを非GUI版に設定
import matplotlib
matplotlib.use('Agg')

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MusicAnalyzer:
    """音楽分析クラス"""
    
    def __init__(self, output_base_dir: str = "music_analysis"):
        """
        初期化
        
        Args:
            output_base_dir: 分析結果の出力ベースディレクトリ
        """
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
        
        # サブディレクトリの設定
        self.results_dir = self.output_base_dir / "results"
        self.visualizations_dir = self.output_base_dir / "visualizations"
        self.sonifications_dir = self.output_base_dir / "sonifications"
        self.demix_dir = self.output_base_dir / "demix"
        self.spectrograms_dir = self.output_base_dir / "spectrograms"
        self.cache_dir = self.output_base_dir / "cache"
        
        # ディレクトリ作成
        for dir_path in [self.results_dir, self.visualizations_dir, self.sonifications_dir,
                        self.demix_dir, self.spectrograms_dir, self.cache_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # allin1ライブラリの遅延インポート
        self._allin1 = None
        
        # UI同期設定
        self.ui_dir = Path("ui")
        self.ui_struct_dir = self.ui_dir / "static" / "struct"
        self.ui_audio_dir = self.ui_dir / "static" / "audio"
    
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
            # 分析実行
            result = self.allin1.analyze(
                str(audio_path),
                out_dir=str(self.results_dir),
                visualize=str(self.visualizations_dir) if include_visualization else False,
                sonify=str(self.sonifications_dir) if include_sonification else False,
                demix_dir=str(self.demix_dir),
                spec_dir=str(self.spectrograms_dir),
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
    
    def normalize_filename(self, filename: str) -> str:
        """
        ファイル名をMusic-Dissector用に正規化
        
        Args:
            filename: 元のファイル名
            
        Returns:
            正規化されたファイル名
        """
        # 拡張子を除去
        base_name = Path(filename).stem
        
        # 特殊文字を除去・置換
        normalized = base_name.replace(" ", "").replace("-", "").lower()
        
        # 数字プレフィックスを追加（存在しない場合）
        if not normalized[:4].isdigit():
            # ハッシュベースの4桁数字を生成
            import hashlib
            hash_obj = hashlib.md5(normalized.encode())
            hash_hex = hash_obj.hexdigest()
            prefix = str(int(hash_hex[:8], 16))[-4:].zfill(4)
            normalized = f"{prefix}_{normalized}"
        
        return normalized
    
    def sync_to_ui(self, audio_file_path: Union[str, Path], auto_normalize: bool = True) -> bool:
        """
        分析結果をUIディレクトリに同期
        
        Args:
            audio_file_path: 元の音楽ファイルパス
            auto_normalize: ファイル名を自動正規化するか
            
        Returns:
            同期成功時True
        """
        audio_path = Path(audio_file_path)
        
        if not self.ui_dir.exists():
            logger.warning("UIディレクトリが見つかりません。同期をスキップします。")
            return False
        
        # UIディレクトリを作成
        self.ui_struct_dir.mkdir(parents=True, exist_ok=True)
        self.ui_audio_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # ファイル名の正規化
            if auto_normalize:
                base_name = self.normalize_filename(audio_path.name)
            else:
                base_name = audio_path.stem
            
            # JSONファイルの同期
            source_json = self.results_dir / f"{audio_path.stem}.json"
            target_json = self.ui_struct_dir / f"{base_name}.json"
            
            if source_json.exists():
                if target_json.exists():
                    target_json.unlink()  # 既存ファイルを削除
                
                # シンボリックリンクまたはコピー
                try:
                    # 相対パスでシンボリックリンクを作成
                    relative_path = os.path.relpath(source_json, self.ui_struct_dir)
                    target_json.symlink_to(relative_path)
                    logger.info(f"JSONファイルをリンク: {target_json.name}")
                except OSError:
                    # シンボリックリンクが失敗した場合はコピー
                    shutil.copy2(source_json, target_json)
                    logger.info(f"JSONファイルをコピー: {target_json.name}")
            
            # 音源ファイルの同期
            target_audio = self.ui_audio_dir / f"{base_name}{audio_path.suffix}"
            
            if target_audio.exists():
                target_audio.unlink()  # 既存ファイルを削除
            
            try:
                # 相対パスでシンボリックリンクを作成
                relative_path = os.path.relpath(audio_path, self.ui_audio_dir)
                target_audio.symlink_to(relative_path)
                logger.info(f"音源ファイルをリンク: {target_audio.name}")
            except OSError:
                # シンボリックリンクが失敗した場合はコピー
                shutil.copy2(audio_path, target_audio)
                logger.info(f"音源ファイルをコピー: {target_audio.name}")
            
            logger.info(f"🎵 UI同期完了: {base_name}")
            return True
            
        except Exception as e:
            logger.error(f"UI同期エラー: {e}")
            return False
    
    def sync_all_to_ui(self) -> int:
        """
        全ての分析結果をUIに同期
        
        Returns:
            同期されたファイル数
        """
        if not self.ui_dir.exists():
            logger.warning("UIディレクトリが見つかりません。")
            return 0
        
        synced_count = 0
        
        # 結果ディレクトリ内のJSONファイルを検索
        for json_file in self.results_dir.glob("*.json"):
            # 対応する音源ファイルを検索
            base_name = json_file.stem
            
            # 一般的な音源ファイル拡張子で検索
            audio_extensions = ['.mp3', '.wav', '.m4a', '.ogg', '.flac']
            audio_file = None
            
            # module/sample_data/ ディレクトリで検索
            sample_dir = Path("module/sample_data")
            if sample_dir.exists():
                for ext in audio_extensions:
                    candidate = sample_dir / f"{base_name}{ext}"
                    if candidate.exists():
                        audio_file = candidate
                        break
            
            if audio_file:
                if self.sync_to_ui(audio_file):
                    synced_count += 1
            else:
                logger.warning(f"対応する音源ファイルが見つかりません: {base_name}")
        
        logger.info(f"🎵 一括UI同期完了: {synced_count}件")
        return synced_count

def main():
    """テスト実行"""
    print("🎵 音楽分析モジュールテスト（新ディレクトリ構造）")
    print("=" * 50)
    
    # 分析器の初期化（新しいディレクトリ構造）
    analyzer = MusicAnalyzer("music_analysis")
    
    print(f"📂 出力ディレクトリ構造:")
    print(f"  ベース: {analyzer.output_base_dir}")
    print(f"  結果: {analyzer.results_dir}")
    print(f"  可視化: {analyzer.visualizations_dir}")
    print(f"  音響化: {analyzer.sonifications_dir}")
    print(f"  音源分離: {analyzer.demix_dir}")
    print(f"  スペクトログラム: {analyzer.spectrograms_dir}")
    print(f"  キャッシュ: {analyzer.cache_dir}")
    
    # サンプルファイルの分析
    sample_file = "module/sample_data/1-03 Additional Memory.m4a"
    
    if Path(sample_file).exists():
        print(f"\n📁 分析対象: {Path(sample_file).name}")
        
        # 既存結果の読み込みテスト
        json_file = analyzer.results_dir / "1-03 Additional Memory.json"
        if json_file.exists():
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
                
                # ファイル存在確認
                print(f"\n📂 生成ファイル確認:")
                files_to_check = [
                    ("JSON結果", json_file),
                    ("アクティベーション", analyzer.results_dir / "1-03 Additional Memory.activ.npz"),
                    ("エンベディング", analyzer.results_dir / "1-03 Additional Memory.embed.npy"),
                    ("可視化PDF", analyzer.visualizations_dir / "1-03 Additional Memory.pdf"),
                    ("スペクトログラム", analyzer.spectrograms_dir / "1-03 Additional Memory.npy"),
                ]
                
                for desc, filepath in files_to_check:
                    if filepath.exists():
                        size_mb = filepath.stat().st_size / (1024 * 1024)
                        print(f"  ✅ {desc}: {size_mb:.1f}MB")
                    else:
                        print(f"  ❌ {desc}: 見つかりません")
                        
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
    
    # UI同期テスト
    if analyzer.ui_dir.exists():
        print(f"\n🔄 UI同期テスト")
        synced_count = analyzer.sync_all_to_ui()
        print(f"✅ UI同期完了: {synced_count}件")
    else:
        print(f"\n⚠️  UIディレクトリが見つかりません: {analyzer.ui_dir}")
    
    print("\n🎉 音楽分析モジュールテスト完了")

if __name__ == "__main__":
    main()
