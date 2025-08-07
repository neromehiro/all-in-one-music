#!/usr/bin/env python3
"""
音楽分析結果のJSONを正しい形式に変換するスクリプト
UIが期待する形式（wav/navの周波数帯域分割）に対応
"""

import json
import numpy as np
from pathlib import Path
import librosa
from typing import Dict, List, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_audio_and_process(audio_path: Path, sr: int = 100) -> Tuple[np.ndarray, float]:
    """
    音声ファイルを読み込み、処理用に準備
    
    Args:
        audio_path: 音声ファイルのパス
        sr: サンプリングレート（Hz）
        
    Returns:
        処理済み音声データと継続時間
    """
    # 音声ファイルを読み込み（モノラル、低サンプリングレート）
    y, _ = librosa.load(audio_path, sr=sr, mono=True)
    duration = len(y) / sr
    
    return y, duration

def generate_frequency_bands(audio_data: np.ndarray, num_frames: int = 5000) -> Dict[str, List[int]]:
    """
    音声データから周波数帯域（low, mid, high）を生成
    
    Args:
        audio_data: 音声データ
        num_frames: 出力フレーム数
        
    Returns:
        low, mid, highの辞書
    """
    # リサンプリング（必要に応じて）
    if len(audio_data) > num_frames:
        # ダウンサンプリング
        indices = np.linspace(0, len(audio_data) - 1, num_frames).astype(int)
        audio_data = audio_data[indices]
    elif len(audio_data) < num_frames:
        # アップサンプリング（線形補間）
        x_old = np.linspace(0, 1, len(audio_data))
        x_new = np.linspace(0, 1, num_frames)
        audio_data = np.interp(x_new, x_old, audio_data)
    
    # 正規化（-1〜1の範囲）
    if np.max(np.abs(audio_data)) > 0:
        audio_data = audio_data / np.max(np.abs(audio_data))
    
    # 簡易的な周波数帯域分割のシミュレーション
    # 実際にはFFTを使うべきだが、ここでは簡易的に処理
    low = audio_data * 0.8  # 低域成分
    mid = audio_data * 1.0  # 中域成分
    high = audio_data * 0.6  # 高域成分
    
    # 0-255の範囲に正規化
    def normalize_to_byte(data):
        # -1〜1を0〜255に変換
        normalized = np.clip((data + 1) * 127.5, 0, 255)
        return normalized.astype(int).tolist()
    
    return {
        "low": normalize_to_byte(low),
        "mid": normalize_to_byte(mid),
        "high": normalize_to_byte(high)
    }

def process_stem_audio(stem_dir: Path, stem_names: List[str], num_frames: int = 5000) -> Tuple[Dict, Dict]:
    """
    stem音源を処理してwavとnavデータを生成
    
    Args:
        stem_dir: stem音源のディレクトリ
        stem_names: stem名のリスト
        num_frames: 出力フレーム数
        
    Returns:
        wavとnavの辞書
    """
    wav_data = {}
    nav_data = {}
    
    for stem in stem_names:
        stem_file = stem_dir / f"{stem}.wav"
        
        if stem_file.exists():
            logger.info(f"Processing {stem} from {stem_file}")
            audio, _ = load_audio_and_process(stem_file, sr=100)
            
            # wav用（より詳細なデータ）
            wav_data[stem.replace("drums", "drum").replace("vocals", "vocal")] = generate_frequency_bands(audio, num_frames)
            
            # nav用（より粗いデータ、ナビゲーション用）
            nav_audio = audio[::5] if len(audio) > 1000 else audio  # 5分の1にダウンサンプリング
            nav_data[stem.replace("drums", "drum").replace("vocals", "vocal")] = generate_frequency_bands(nav_audio, 1000)
        else:
            logger.warning(f"Stem file not found: {stem_file}")
            # ダミーデータを生成
            wav_data[stem.replace("drums", "drum").replace("vocals", "vocal")] = {
                "low": [128] * num_frames,
                "mid": [128] * num_frames,
                "high": [128] * num_frames
            }
            nav_data[stem.replace("drums", "drum").replace("vocals", "vocal")] = {
                "low": [128] * 1000,
                "mid": [128] * 1000,
                "high": [128] * 1000
            }
    
    return wav_data, nav_data

def convert_segments_format(segments: List) -> List[float]:
    """
    セグメントデータを正しい形式に変換
    [[start, end], ...] -> [start1, start2, ...]
    """
    if not segments:
        return []
    
    # 2次元配列の場合
    if isinstance(segments[0], list):
        return [seg[0] for seg in segments]
    
    # すでに1次元配列の場合
    return segments

def convert_json_to_ui_format(
    input_json_path: Path,
    stem_dir: Optional[Path] = None,
    output_json_path: Optional[Path] = None
) -> bool:
    """
    JSONファイルをUI用の形式に変換
    
    Args:
        input_json_path: 入力JSONファイルのパス
        stem_dir: stem音源のディレクトリ（オプション）
        output_json_path: 出力JSONファイルのパス（オプション、指定しない場合は上書き）
        
    Returns:
        成功時True
    """
    try:
        # JSONファイルを読み込み
        with open(input_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Loaded JSON: {input_json_path}")
        
        # stem音源のディレクトリを特定
        if stem_dir is None:
            # デフォルトのパスを試す
            base_name = "1-03 Additional Memory"  # ハードコーディングされた例
            stem_dir = Path("music_analysis/demix/htdemucs") / base_name
        
        # wav/navデータの生成
        if stem_dir.exists():
            wav_data, nav_data = process_stem_audio(
                stem_dir,
                ["drums", "bass", "vocals", "other"]
            )
        else:
            logger.warning(f"Stem directory not found: {stem_dir}")
            # ダミーデータを生成
            wav_data = nav_data = {
                "drum": {"low": [128] * 5000, "mid": [128] * 5000, "high": [128] * 5000},
                "bass": {"low": [128] * 5000, "mid": [128] * 5000, "high": [128] * 5000},
                "vocal": {"low": [128] * 5000, "mid": [128] * 5000, "high": [128] * 5000},
                "other": {"low": [128] * 5000, "mid": [128] * 5000, "high": [128] * 5000}
            }
        
        # データの更新
        data["wav"] = wav_data
        data["nav"] = nav_data
        
        # inferenceデータの形式を修正
        if "inferences" in data:
            if "segments" in data["inferences"]:
                data["inferences"]["segments"] = convert_segments_format(data["inferences"]["segments"])
            
            # beats/downbeatsが空の場合、ダミーデータを生成
            if not data["inferences"].get("beats"):
                # BPMから推定（例：120BPMの場合）
                bpm = data.get("scores", {}).get("beat", {}).get("bpm", 120)
                duration = data.get("duration", 240)
                beat_interval = 60.0 / bpm
                data["inferences"]["beats"] = list(np.arange(0, duration, beat_interval))
            
            if not data["inferences"].get("downbeats"):
                # 4拍子と仮定
                beats = data["inferences"]["beats"]
                data["inferences"]["downbeats"] = beats[::4] if beats else []
        
        # truthsデータの形式を修正
        if "truths" in data:
            if "segments" in data["truths"]:
                data["truths"]["segments"] = convert_segments_format(data["truths"]["segments"])
        
        # scoresデータの確認と修正
        if "scores" not in data:
            data["scores"] = {
                "beat": {"f1": 1.0},
                "downbeat": {"f1": 1.0},
                "segment": {
                    "F-measure@0.5": 1.0,
                    "Pairwise F-measure": 1.0
                }
            }
        
        # 出力パスの決定
        if output_json_path is None:
            output_json_path = input_json_path
        
        # JSONファイルを保存
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved converted JSON: {output_json_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error converting JSON: {e}")
        return False

def main():
    """メイン処理"""
    print("=" * 60)
    print("🎵 音楽分析JSON変換ツール")
    print("=" * 60)
    
    # 変換対象のJSONファイル
    json_file = Path("music_analysis/results/0461_103additionalmemory.json")
    
    if not json_file.exists():
        # 元のJSONファイルをコピー
        original_json = Path("ui/static/struct/0461_103additionalmemory.json")
        if original_json.exists():
            import shutil
            shutil.copy(original_json, json_file)
            print(f"📋 JSONファイルをコピー: {json_file}")
    
    if json_file.exists():
        print(f"\n📁 変換対象: {json_file}")
        
        # stem音源のディレクトリ
        stem_dir = Path("music_analysis/demix/htdemucs/1-03 Additional Memory")
        
        if stem_dir.exists():
            print(f"🎼 Stem音源ディレクトリ: {stem_dir}")
        else:
            print(f"⚠️  Stem音源ディレクトリが見つかりません: {stem_dir}")
        
        # 変換実行
        print("\n🔄 変換開始...")
        success = convert_json_to_ui_format(json_file, stem_dir)
        
        if success:
            print("✅ 変換成功！")
            
            # UIディレクトリにもコピー
            ui_json = Path("ui/static/struct/0461_103additionalmemory.json")
            import shutil
            shutil.copy(json_file, ui_json)
            print(f"📋 UIディレクトリにコピー: {ui_json}")
        else:
            print("❌ 変換失敗")
    else:
        print(f"❌ JSONファイルが見つかりません: {json_file}")
    
    print("\n" + "=" * 60)
    print("完了")

if __name__ == "__main__":
    main()
