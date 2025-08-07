#!/usr/bin/env python3
"""
シンプルな音楽分析ツール
音声ファイルからJSON（分析結果）とStem音声を出力
Music-Dissector形式への自動変換機能付き
"""

import json
import sys
from pathlib import Path
from typing import Optional, Dict, Union
import logging

# convert_to_music_dissectorをインポート
sys.path.append(str(Path(__file__).parent.parent))
from convert_to_music_dissector import convert_to_music_dissector

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleAnalyzer:
    """シンプルな音楽分析クラス"""
    
    def __init__(self, output_dir: str = "output"):
        """
        初期化
        
        Args:
            output_dir: 出力ディレクトリ（デフォルト: output）
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
                logger.info("✅ allin1ライブラリのインポート成功")
            except ImportError as e:
                logger.error(f"❌ allin1ライブラリのインポートに失敗: {e}")
                logger.error("pip install allin1 を実行してください")
                sys.exit(1)
        return self._allin1
    
    def analyze(self, audio_path: Union[str, Path]) -> Optional[Dict]:
        """
        音声ファイルを分析してJSONとStem音声を出力
        Music-Dissector形式への変換も自動実行
        
        Args:
            audio_path: 音声ファイルのパス
            
        Returns:
            分析結果の辞書（エラー時はNone）
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            logger.error(f"❌ ファイルが見つかりません: {audio_path}")
            return None
        
        logger.info(f"🎵 分析開始: {audio_path.name}")
        
        try:
            # 曲名ディレクトリを作成
            track_dir = self.output_dir / audio_path.stem
            track_dir.mkdir(parents=True, exist_ok=True)
            
            # 音源分離の出力先（一時的）
            temp_demix_dir = self.output_dir / "temp_demix"
            
            # All-In-Oneで分析実行
            result = self.allin1.analyze(
                str(audio_path),
                demix_dir=str(temp_demix_dir),
                keep_byproducts=True,  # 音源分離ファイルを保持
                device='cpu'  # GPUがない環境でも動作
            )
            
            # 分析結果を辞書形式に変換
            analysis_data = {
                "file_name": audio_path.name,
                "file_path": str(audio_path.absolute()),
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
            
            # JSONファイルとして保存
            json_output_path = track_dir / f"{audio_path.stem}.json"
            with open(json_output_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ JSON保存完了: {json_output_path}")
            
            # Stem音声の移動・整理
            htdemucs_dir = temp_demix_dir / "htdemucs" / audio_path.stem
            stem_output_dir = track_dir / "stems"
            
            if htdemucs_dir.exists():
                # 正しい場所に移動
                if stem_output_dir.exists():
                    import shutil
                    shutil.rmtree(stem_output_dir)
                htdemucs_dir.rename(stem_output_dir)
                
                # 一時ディレクトリを削除
                htdemucs_parent = temp_demix_dir / "htdemucs"
                if htdemucs_parent.exists() and not any(htdemucs_parent.iterdir()):
                    htdemucs_parent.rmdir()
                if temp_demix_dir.exists() and not any(temp_demix_dir.iterdir()):
                    temp_demix_dir.rmdir()
                
                logger.info(f"✅ Stem音声保存完了: {stem_output_dir}")
                
                # 保存されたStemファイルを確認
                for stem_file in stem_output_dir.glob("*.wav"):
                    logger.info(f"  - {stem_file.name}")
            
            # サマリー表示
            logger.info(f"\n📊 分析結果サマリー:")
            logger.info(f"  BPM: {result.bpm}")
            logger.info(f"  ビート数: {len(result.beats)}")
            logger.info(f"  ダウンビート数: {len(result.downbeats)}")
            logger.info(f"  セグメント数: {len(result.segments)}")
            
            # セグメント情報
            logger.info(f"\n🎼 セグメント構成:")
            for seg in result.segments:
                duration = seg.end - seg.start
                logger.info(f"  {seg.label}: {seg.start:.1f}s - {seg.end:.1f}s ({duration:.1f}s)")
            
            # Music-Dissector形式への変換
            logger.info(f"\n🔄 Music-Dissector形式への変換開始...")
            try:
                music_dissector_path = convert_to_music_dissector(json_output_path)
                logger.info(f"✅ Music-Dissector形式への変換完了")
            except Exception as e:
                logger.error(f"❌ Music-Dissector形式への変換エラー: {e}")
                import traceback
                traceback.print_exc()
            
            return analysis_data
            
        except Exception as e:
            logger.error(f"❌ 分析エラー: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def batch_analyze(self, audio_files: list) -> list:
        """
        複数の音声ファイルを一括分析
        
        Args:
            audio_files: 音声ファイルパスのリスト
            
        Returns:
            分析結果のリスト
        """
        results = []
        total = len(audio_files)
        
        for i, audio_file in enumerate(audio_files, 1):
            logger.info(f"\n{'='*50}")
            logger.info(f"📁 処理中 ({i}/{total}): {Path(audio_file).name}")
            logger.info(f"{'='*50}")
            
            result = self.analyze(audio_file)
            if result:
                results.append(result)
        
        logger.info(f"\n✅ 一括分析完了: {len(results)}/{total} ファイル成功")
        return results


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="音声ファイルを分析してJSONとStem音声を出力"
    )
    parser.add_argument(
        "audio_files",
        nargs="+",
        help="分析する音声ファイル（複数指定可）"
    )
    parser.add_argument(
        "-o", "--output",
        default="output",
        help="出力ディレクトリ（デフォルト: output）"
    )
    
    args = parser.parse_args()
    
    # 分析実行
    analyzer = SimpleAnalyzer(args.output)
    
    if len(args.audio_files) == 1:
        # 単一ファイル
        result = analyzer.analyze(args.audio_files[0])
        if result:
            logger.info(f"\n✅ 分析完了！")
            logger.info(f"📁 出力先: {analyzer.output_dir}")
            logger.info(f"📂 ディレクトリ構造:")
            logger.info(f"  {analyzer.output_dir}/")
            logger.info(f"  └── [曲名]/")
            logger.info(f"      ├── [曲名].json")
            logger.info(f"      ├── stems/")
            logger.info(f"      │   ├── bass.wav")
            logger.info(f"      │   ├── drums.wav")
            logger.info(f"      │   ├── other.wav")
            logger.info(f"      │   └── vocals.wav")
            logger.info(f"      └── music-dissector/")
            logger.info(f"          ├── data/")
            logger.info(f"          │   ├── [曲名].json.gz")
            logger.info(f"          │   └── [曲名].json")
            logger.info(f"          ├── mixdown/")
            logger.info(f"          │   └── [曲名].mp3")
            logger.info(f"          └── demixed/")
            logger.info(f"              └── [曲名]/")
            logger.info(f"                  ├── bass.mp3")
            logger.info(f"                  ├── drum.mp3")
            logger.info(f"                  ├── other.mp3")
            logger.info(f"                  └── vocal.mp3")
    else:
        # 複数ファイル
        results = analyzer.batch_analyze(args.audio_files)
        if results:
            logger.info(f"\n✅ 全ての分析が完了！")
            logger.info(f"📁 出力先: {analyzer.output_dir}")
            logger.info(f"📂 ディレクトリ構造:")
            logger.info(f"  {analyzer.output_dir}/")
            logger.info(f"  └── [曲名]/")
            logger.info(f"      ├── [曲名].json")
            logger.info(f"      ├── stems/")
            logger.info(f"      │   ├── bass.wav")
            logger.info(f"      │   ├── drums.wav")
            logger.info(f"      │   ├── other.wav")
            logger.info(f"      │   └── vocals.wav")
            logger.info(f"      └── music-dissector/")
            logger.info(f"          ├── data/")
            logger.info(f"          │   ├── [曲名].json.gz")
            logger.info(f"          │   └── [曲名].json")
            logger.info(f"          ├── mixdown/")
            logger.info(f"          │   └── [曲名].mp3")
            logger.info(f"          └── demixed/")
            logger.info(f"              └── [曲名]/")
            logger.info(f"                  ├── bass.mp3")
            logger.info(f"                  ├── drum.mp3")
            logger.info(f"                  ├── other.mp3")
            logger.info(f"                  └── vocal.mp3")


if __name__ == "__main__":
    main()
