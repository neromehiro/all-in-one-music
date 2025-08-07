#!/usr/bin/env python3
"""
allin1の出力をMusic-Dissector形式に変換するスクリプト
"""

import json
import gzip
import re
from pathlib import Path
import soundfile as sf
import numpy as np
import librosa
import shutil
import subprocess

def extract_audio_features(audio_path, target_length=46806):
    """
    音声ファイルから周波数帯域別の特徴量を抽出
    
    Args:
        audio_path: 音声ファイルのパス
        target_length: 出力配列の長さ
    
    Returns:
        dict: low, mid, highの周波数帯域別特徴量
    """
    try:
        # 音声ファイルを読み込み
        y, sr = librosa.load(audio_path, sr=None)
        
        # 時間軸方向のサンプル数を計算
        hop_length = len(y) // target_length
        if hop_length < 1:
            hop_length = 1
        
        # スペクトログラムを計算
        D = np.abs(librosa.stft(y, hop_length=hop_length))
        
        # 周波数帯域を3つに分割
        freq_bins = D.shape[0]
        low_end = freq_bins // 3
        mid_end = 2 * freq_bins // 3
        
        # 各帯域のエネルギーを計算
        low_energy = np.mean(D[:low_end, :], axis=0)
        mid_energy = np.mean(D[low_end:mid_end, :], axis=0)
        high_energy = np.mean(D[mid_end:, :], axis=0)
        
        # 正規化（0-255の範囲に）
        def normalize(arr):
            if arr.max() > 0:
                # 0-255の範囲に正規化して整数に変換
                normalized = (arr / arr.max() * 255).astype(int)
                return normalized.tolist()
            return arr.tolist()
        
        # target_lengthに合わせてリサンプリング
        def resample_to_length(arr, target_len):
            if len(arr) == target_len:
                return arr
            indices = np.linspace(0, len(arr) - 1, target_len)
            return np.interp(indices, np.arange(len(arr)), arr).tolist()
        
        return {
            "low": resample_to_length(normalize(low_energy), target_length),
            "mid": resample_to_length(normalize(mid_energy), target_length),
            "high": resample_to_length(normalize(high_energy), target_length)
        }
    except Exception as e:
        print(f"警告: {audio_path}の特徴抽出に失敗しました: {e}")
        # エラーの場合はゼロ配列を返す
        return {
            "low": [0.0] * target_length,
            "mid": [0.0] * target_length,
            "high": [0.0] * target_length
        }

def calculate_f1_score(pred_times, true_times, tolerance=0.07):
    """
    F1スコアを計算
    
    Args:
        pred_times: 予測されたタイムスタンプのリスト
        true_times: 正解のタイムスタンプのリスト
        tolerance: 許容誤差（秒）
    
    Returns:
        float: F1スコア
    """
    if not pred_times or not true_times:
        return 0.0
    
    # 予測と正解が同じ場合は1.0を返す
    if pred_times == true_times:
        return 1.0
    
    # 簡易的なF1計算（実際の実装では、より厳密な計算が必要）
    matched = 0
    for pred in pred_times:
        for true in true_times:
            if abs(pred - true) <= tolerance:
                matched += 1
                break
    
    if matched == 0:
        return 0.0
    
    precision = matched / len(pred_times)
    recall = matched / len(true_times)
    
    if precision + recall == 0:
        return 0.0
    
    return 2 * (precision * recall) / (precision + recall)

def convert_wav_to_mp3(wav_path, mp3_path):
    """
    WAVファイルをMP3に変換
    
    Args:
        wav_path: 入力WAVファイルのパス
        mp3_path: 出力MP3ファイルのパス
    """
    try:
        # ffmpegを使用してWAVをMP3に変換
        cmd = [
            'ffmpeg', '-i', str(wav_path),
            '-acodec', 'mp3', '-ab', '192k',
            '-y',  # 既存ファイルを上書き
            str(mp3_path)
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"  ✅ MP3変換完了: {mp3_path.name}")
    except subprocess.CalledProcessError as e:
        print(f"  ❌ MP3変換エラー: {e}")
        # ffmpegがない場合は、WAVファイルをそのままコピー（拡張子は.mp3にする）
        shutil.copy2(wav_path, mp3_path)
        print(f"  ⚠️  WAVファイルをコピー: {mp3_path.name}")
    except FileNotFoundError:
        print(f"  ❌ ffmpegが見つかりません。WAVファイルをコピーします。")
        shutil.copy2(wav_path, mp3_path)

def convert_to_music_dissector(input_path, output_path=None):
    """
    allin1のJSON出力をMusic-Dissector形式に変換
    
    Args:
        input_path: 入力JSONファイルのパス
        output_path: 出力ディレクトリのパス（省略時は同じディレクトリにmusic-dissectorフォルダを作成）
    """
    input_path = Path(input_path)
    
    # 出力ディレクトリの設定
    if output_path is None:
        output_dir = input_path.parent / "music-dissector"
    else:
        output_dir = Path(output_path)
    
    # 必要なディレクトリを作成
    data_dir = output_dir / "data"
    mixdown_dir = output_dir / "mixdown"
    demixed_dir = output_dir / "demixed"
    
    data_dir.mkdir(parents=True, exist_ok=True)
    mixdown_dir.mkdir(parents=True, exist_ok=True)
    demixed_dir.mkdir(parents=True, exist_ok=True)
    
    # 元のJSONを読み込み
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 音声ファイルのパスを取得
    audio_path_str = data.get('file_path', data.get('file_name', ''))
    audio_path = Path(audio_path_str)
    
    # IDを生成（ファイル名から非英数字を除去し、数字を先頭に追加）
    file_id = re.sub(r'\W+', '', audio_path.stem.lower())
    # Music-Dissectorのフォーマットに合わせて数字を追加
    file_id = f"0000_{file_id}"
    
    # 音声ファイルの長さを取得（複数の方法を試す）
    duration = None
    
    # 方法1: 元の音声ファイルから取得
    possible_audio_paths = [
        audio_path,  # 絶対パス
        input_path.parent / audio_path.name,  # JSONと同じディレクトリ
        Path.cwd() / audio_path.name,  # カレントディレクトリ
    ]
    
    # file_pathが絶対パスの場合、その親ディレクトリも探索
    if audio_path.is_absolute():
        # ../module/sample_data/のようなパスも試す
        possible_audio_paths.append(Path.cwd() / "module" / "sample_data" / audio_path.name)
        possible_audio_paths.append(input_path.parent.parent / "module" / "sample_data" / audio_path.name)
    
    for test_path in possible_audio_paths:
        if test_path.exists():
            try:
                print(f"音声ファイル発見: {test_path}")
                info = sf.info(test_path)
                duration = info.duration
                print(f"  長さ: {duration:.2f}秒")
                break
            except Exception as e:
                print(f"  読み込みエラー: {e}")
    
    # 方法2: ステムファイルから取得
    if duration is None:
        stems_dir = input_path.parent / "stems"
        if stems_dir.exists():
            stem_files = list(stems_dir.glob("*.wav"))
            if stem_files:
                try:
                    print(f"ステムファイルから長さを取得: {stem_files[0]}")
                    info = sf.info(stem_files[0])
                    duration = info.duration
                    print(f"  長さ: {duration:.2f}秒")
                except Exception as e:
                    print(f"  読み込みエラー: {e}")
    
    # 方法3: 既存のMP3ファイルから取得（再変換の場合）
    if duration is None:
        mp3_paths = [
            output_dir / "mixdown" / f"{input_path.stem}.mp3",
            output_dir / "demixed" / input_path.stem / "bass.mp3"
        ]
        for mp3_path in mp3_paths:
            if mp3_path.exists():
                try:
                    print(f"既存のMP3から長さを取得: {mp3_path}")
                    info = sf.info(mp3_path)
                    duration = info.duration
                    print(f"  長さ: {duration:.2f}秒")
                    break
                except Exception as e:
                    print(f"  読み込みエラー: {e}")
    
    # 方法4: 最後の手段としてbeatsから推定
    if duration is None:
        print(f"警告: 音声ファイルが見つからないため、beatsから推定")
        if data.get('beats'):
            # 最後のビートから音楽の終わりまでの余裕を考慮
            # 通常、最後のビートから10-30秒程度の余裕がある
            last_beat = data['beats'][-1]
            # 音楽の構造を考慮して、より現実的な推定を行う
            # 一般的に、最後のビートから全体の15-20%程度の余裕がある
            estimated_ratio = 1.17  # 17%の余裕
            duration = last_beat * estimated_ratio
            print(f"  最後のビート: {last_beat:.2f}秒")
            print(f"  推定duration: {duration:.2f}秒")
        else:
            duration = 240.0  # デフォルト値
            print(f"  デフォルト値使用: {duration:.2f}秒")
    
    # 配列の長さを計算（100Hzサンプリングを想定）
    array_length = int(duration * 100)
    
    # Music-Dissector形式のデータ構造を作成
    music_dissector_data = {
        "nav": {
            "bass": {"low": [], "mid": [], "high": []},
            "drum": {"low": [], "mid": [], "high": []},
            "other": {"low": [], "mid": [], "high": []},
            "vocal": {"low": [], "mid": [], "high": []}
        },
        "wav": {
            "bass": {"low": [], "mid": [], "high": []},
            "drum": {"low": [], "mid": [], "high": []},
            "other": {"low": [], "mid": [], "high": []},
            "vocal": {"low": [], "mid": [], "high": []}
        },
        "duration": duration,
        "scores": {},
        "id": file_id,
        "inferences": {},
        "truths": {}
    }
    
    # stemsフォルダのパスを構築
    stems_dir = input_path.parent / "stems"
    
    # 各楽器のステムファイルから特徴量を抽出
    instrument_mapping = {
        "bass": "bass.wav",
        "drum": "drums.wav",  # drumsをdrumにマッピング
        "other": "other.wav",
        "vocal": "vocals.wav"  # vocalsをvocalにマッピング
    }
    
    for instrument, filename in instrument_mapping.items():
        stem_path = stems_dir / filename
        if stem_path.exists():
            print(f"処理中: {stem_path}")
            features = extract_audio_features(stem_path, array_length)
            music_dissector_data["nav"][instrument] = features
            # wavデータはnavと同じにする（簡略化）
            music_dissector_data["wav"][instrument] = features
        else:
            print(f"警告: {stem_path}が見つかりません")
            # ファイルが見つからない場合はゼロ配列
            music_dissector_data["nav"][instrument] = {
                "low": [0.0] * array_length,
                "mid": [0.0] * array_length,
                "high": [0.0] * array_length
            }
            music_dissector_data["wav"][instrument] = music_dissector_data["nav"][instrument]
    
    # 既存のデータをinferencesに移動
    music_dissector_data["inferences"] = {
        "beats": data.get("beats", []),
        "downbeats": data.get("downbeats", []),
        "segments": [],
        "labels": []
    }
    
    # セグメント情報を変換（オブジェクトから時刻のリストとラベルのリストに分離）
    if data.get("segments"):
        segments_times = []
        labels = []
        for i, segment in enumerate(data["segments"]):
            segments_times.append(segment["start"])
            labels.append(segment["label"])
        # 最後のセグメントの終了時刻も追加
        if data["segments"]:
            segments_times.append(data["segments"][-1]["end"])
        
        music_dissector_data["inferences"]["segments"] = segments_times
        music_dissector_data["inferences"]["labels"] = labels
    
    # truthsデータを追加（現時点ではinferencesと同じデータを使用）
    music_dissector_data["truths"] = {
        "beats": music_dissector_data["inferences"]["beats"].copy(),
        "downbeats": music_dissector_data["inferences"]["downbeats"].copy(),
        "segments": music_dissector_data["inferences"]["segments"].copy(),
        "labels": music_dissector_data["inferences"]["labels"].copy()
    }
    
    # スコアを計算（truthsとinferencesが同じなので1.0）
    music_dissector_data["scores"] = {
        "beat": {
            "f1": calculate_f1_score(
                music_dissector_data["inferences"]["beats"],
                music_dissector_data["truths"]["beats"]
            )
        },
        "downbeat": {
            "f1": calculate_f1_score(
                music_dissector_data["inferences"]["downbeats"],
                music_dissector_data["truths"]["downbeats"]
            )
        },
        "segment": {
            "F-measure@0.5": 1.0,  # 簡略化のため1.0に設定
            "Pairwise F-measure": 1.0  # 簡略化のため1.0に設定
        }
    }
    
    # 音声ファイルをMP3形式で配置
    print("\n🎵 音声ファイルの変換と配置...")
    
    # ミックスダウンファイル
    track_name = input_path.stem
    mixdown_mp3 = mixdown_dir / f"{track_name}.mp3"
    
    # 元の音声ファイルが存在する場合
    if audio_path.exists():
        if audio_path.suffix.lower() == '.mp3':
            # すでにMP3の場合はコピー
            shutil.copy2(audio_path, mixdown_mp3)
            print(f"  ✅ MP3コピー完了: {mixdown_mp3.name}")
        else:
            # MP3に変換
            convert_wav_to_mp3(audio_path, mixdown_mp3)
    
    # ステムファイルの変換と配置
    demixed_track_dir = demixed_dir / track_name
    demixed_track_dir.mkdir(exist_ok=True)
    
    for instrument, filename in instrument_mapping.items():
        stem_wav = stems_dir / filename
        stem_mp3 = demixed_track_dir / f"{instrument}.mp3"
        
        if stem_wav.exists():
            convert_wav_to_mp3(stem_wav, stem_mp3)
    
    # JSONファイルをgzip圧縮して保存
    json_gz_path = data_dir / f"{track_name}.json.gz"
    
    print(f"\n📦 JSONファイルを圧縮中...")
    with gzip.open(json_gz_path, 'wt', encoding='utf-8') as f:
        json.dump(music_dissector_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 変換完了: {json_gz_path}")
    
    # 通常のJSONファイルも保存（デバッグ用）
    json_path = data_dir / f"{track_name}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(music_dissector_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📂 出力ディレクトリ構造:")
    print(f"  {output_dir}/")
    print(f"  ├── data/")
    print(f"  │   ├── {track_name}.json.gz")
    print(f"  │   └── {track_name}.json (デバッグ用)")
    print(f"  ├── mixdown/")
    print(f"  │   └── {track_name}.mp3")
    print(f"  └── demixed/")
    print(f"      └── {track_name}/")
    print(f"          ├── drum.mp3")
    print(f"          ├── bass.mp3")
    print(f"          ├── vocal.mp3")
    print(f"          └── other.mp3")
    
    return json_gz_path

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法: python convert_to_music_dissector.py <input.json> [output_dir]")
        print("例: python convert_to_music_dissector.py all-in-one/output_test/benefits/benefits.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    convert_to_music_dissector(input_file, output_dir)
