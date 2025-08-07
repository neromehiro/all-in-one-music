#!/usr/bin/env python3
"""
大きなJSONファイルから各キーの先頭10個だけを抽出して
比較用の小さなJSONファイルを作成するスクリプト
"""

import json
from pathlib import Path
from typing import Any, Dict
import sys

def truncate_data(data: Any, max_items: int = 10) -> Any:
    """
    データを再帰的に処理して、配列の要素を最大max_items個に制限する
    """
    if isinstance(data, dict):
        # 辞書の場合、各値を再帰的に処理
        result = {}
        for key, value in data.items():
            result[key] = truncate_data(value, max_items)
        return result
    
    elif isinstance(data, list):
        # リストの場合
        if len(data) == 0:
            return data
        
        # 最初の要素をチェック
        first_elem = data[0]
        
        # 数値の配列の場合（1次元配列）
        if isinstance(first_elem, (int, float)):
            truncated = data[:max_items]
            return {
                "_type": "array",
                "_original_length": len(data),
                "_truncated": True if len(data) > max_items else False,
                "data": truncated
            }
        
        # 2次元配列の場合
        elif isinstance(first_elem, list):
            # 各サブ配列も制限
            truncated = []
            for i, subarray in enumerate(data[:max_items]):
                if isinstance(subarray, list) and len(subarray) > 0:
                    if isinstance(subarray[0], (int, float)):
                        # 数値の配列
                        truncated.append({
                            "_type": "array",
                            "_original_length": len(subarray),
                            "_truncated": True if len(subarray) > max_items else False,
                            "data": subarray[:max_items]
                        })
                    else:
                        # さらにネストされた配列
                        truncated.append(truncate_data(subarray, max_items))
                else:
                    truncated.append(subarray)
            
            return {
                "_type": "2d_array",
                "_original_shape": f"[{len(data)}, varied]",
                "_truncated_shape": f"[{len(truncated)}, {max_items}]",
                "data": truncated
            }
        
        # その他のリスト（オブジェクトの配列など）
        else:
            truncated = []
            for item in data[:max_items]:
                truncated.append(truncate_data(item, max_items))
            return {
                "_type": "list",
                "_original_length": len(data),
                "_truncated": True if len(data) > max_items else False,
                "data": truncated
            }
    
    # スカラー値はそのまま返す
    else:
        return data

def create_comparison_files():
    """
    成功JSONと失敗JSONから比較用ファイルを作成
    """
    # ファイルパス
    success_path = Path("success.json")
    fail_path = Path("../ui/static/struct/0461_103additionalmemory.json")
    
    # 出力ファイルパス
    success_sample_path = Path("success_sample.json")
    fail_sample_path = Path("fail_sample.json")
    comparison_path = Path("comparison.json")
    
    print("=" * 80)
    print("JSON サンプル抽出ツール")
    print("=" * 80)
    
    # ファイルの存在確認
    if not success_path.exists():
        print(f"❌ ファイルが見つかりません: {success_path}")
        sys.exit(1)
    if not fail_path.exists():
        print(f"❌ ファイルが見つかりません: {fail_path}")
        sys.exit(1)
    
    print(f"✅ 成功JSON: {success_path}")
    print(f"❌ 失敗JSON: {fail_path}")
    print()
    
    # JSONファイルを読み込み
    print("ファイルを読み込み中...")
    
    try:
        with open(success_path, 'r') as f:
            success_data = json.load(f)
        print(f"  成功JSONを読み込みました")
    except Exception as e:
        print(f"  成功JSONの読み込みエラー: {e}")
        sys.exit(1)
    
    try:
        with open(fail_path, 'r') as f:
            fail_data = json.load(f)
        print(f"  失敗JSONを読み込みました")
    except Exception as e:
        print(f"  失敗JSONの読み込みエラー: {e}")
        sys.exit(1)
    
    print()
    print("データを切り詰め中...")
    
    # データを切り詰める
    success_truncated = truncate_data(success_data, max_items=10)
    fail_truncated = truncate_data(fail_data, max_items=10)
    
    # 個別のサンプルファイルを保存
    with open(success_sample_path, 'w') as f:
        json.dump(success_truncated, f, indent=2, ensure_ascii=False)
    print(f"✅ 成功サンプルを保存: {success_sample_path}")
    
    with open(fail_sample_path, 'w') as f:
        json.dump(fail_truncated, f, indent=2, ensure_ascii=False)
    print(f"❌ 失敗サンプルを保存: {fail_sample_path}")
    
    # 比較用ファイルを作成
    comparison = {
        "success": success_truncated,
        "fail": fail_truncated,
        "_metadata": {
            "description": "JSONファイルの比較用サンプル（各配列は最大10要素に制限）",
            "success_source": str(success_path),
            "fail_source": str(fail_path),
            "max_items_per_array": 10
        }
    }
    
    with open(comparison_path, 'w') as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)
    print(f"📊 比較ファイルを保存: {comparison_path}")
    
    print()
    print("=" * 80)
    print("主要な違いの要約")
    print("=" * 80)
    
    # wavセクションの違いを表示
    if 'wav' in success_truncated and 'wav' in fail_truncated:
        print("\n【wav セクション】")
        success_wav = success_truncated['wav']
        fail_wav = fail_truncated['wav']
        
        # キーの比較
        success_wav_keys = set(success_wav.keys())
        fail_wav_keys = set(fail_wav.keys())
        
        print(f"成功JSON wavキー: {sorted(success_wav_keys)}")
        print(f"失敗JSON wavキー: {sorted(fail_wav_keys)}")
        
        # 共通のキーについて型を比較
        common_keys = success_wav_keys & fail_wav_keys
        for key in sorted(common_keys):
            success_type = type(success_wav[key]).__name__
            fail_type = type(fail_wav[key]).__name__
            
            if success_type != fail_type:
                print(f"\n  ⚠️ wav.{key}の型が異なる:")
                print(f"     成功: {success_type}")
                print(f"     失敗: {fail_type}")
            
            # 詳細情報
            if isinstance(success_wav[key], dict) and '_type' in success_wav[key]:
                print(f"\n  wav.{key} (成功):")
                print(f"     タイプ: {success_wav[key].get('_type', 'unknown')}")
                if '_original_length' in success_wav[key]:
                    print(f"     元の長さ: {success_wav[key]['_original_length']}")
                if '_original_shape' in success_wav[key]:
                    print(f"     元の形状: {success_wav[key]['_original_shape']}")
            
            if isinstance(fail_wav[key], dict) and '_type' in fail_wav[key]:
                print(f"\n  wav.{key} (失敗):")
                print(f"     タイプ: {fail_wav[key].get('_type', 'unknown')}")
                if '_original_length' in fail_wav[key]:
                    print(f"     元の長さ: {fail_wav[key]['_original_length']}")
                if '_original_shape' in fail_wav[key]:
                    print(f"     元の形状: {fail_wav[key]['_original_shape']}")
    
    print()
    print("=" * 80)
    print("✅ 完了！")
    print()
    print("作成されたファイル:")
    print(f"  1. {success_sample_path} - 成功JSONのサンプル")
    print(f"  2. {fail_sample_path} - 失敗JSONのサンプル")
    print(f"  3. {comparison_path} - 両方を含む比較ファイル")
    print()
    print("これらのファイルは元のファイルよりもはるかに小さく、")
    print("エディタで開いて比較することができます。")

if __name__ == "__main__":
    create_comparison_files()
