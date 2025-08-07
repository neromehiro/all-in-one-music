#!/usr/bin/env python3
"""
JSONファイルの構造を比較して違いを分析するスクリプト
"""

import json
import numpy as np
from pathlib import Path
from typing import Any, Dict, List, Tuple
import sys

def get_array_info(data: Any) -> str:
    """配列の情報を取得"""
    if isinstance(data, list):
        if len(data) == 0:
            return "empty list"
        
        # 最初の要素で型を判定
        first_elem = data[0]
        
        if isinstance(first_elem, (int, float)):
            # 1次元配列
            return f"1D array [{len(data)}]"
        elif isinstance(first_elem, list):
            # 2次元以上の配列
            if len(first_elem) == 0:
                return f"2D array [{len(data)}, 0]"
            
            # 2次元配列の詳細
            if isinstance(first_elem[0], (int, float)):
                # 各チャンネルの長さを確認
                channel_lengths = [len(ch) for ch in data[:5]]  # 最初の5チャンネルまで
                if len(set(channel_lengths)) == 1:
                    return f"2D array [{len(data)}, {channel_lengths[0]}]"
                else:
                    return f"2D array [{len(data)}, varied: {channel_lengths}]"
            elif isinstance(first_elem[0], list):
                # 3次元配列
                return f"3D array [{len(data)}, {len(first_elem)}, {len(first_elem[0]) if first_elem else 0}]"
            else:
                return f"2D array with {type(first_elem[0]).__name__}"
        else:
            return f"list of {type(first_elem).__name__}"
    elif isinstance(data, dict):
        return f"dict with {len(data)} keys"
    elif isinstance(data, (int, float)):
        return f"number ({data})"
    elif isinstance(data, str):
        return f"string"
    else:
        return type(data).__name__

def compare_structure(obj1: Any, obj2: Any, path: str = "") -> List[Tuple[str, str, str]]:
    """2つのオブジェクトの構造を比較"""
    differences = []
    
    if type(obj1) != type(obj2):
        differences.append((path, get_array_info(obj1), get_array_info(obj2)))
        return differences
    
    if isinstance(obj1, dict):
        all_keys = set(obj1.keys()) | set(obj2.keys())
        for key in sorted(all_keys):
            new_path = f"{path}.{key}" if path else key
            
            if key not in obj1:
                differences.append((new_path, "NOT FOUND", get_array_info(obj2[key])))
            elif key not in obj2:
                differences.append((new_path, get_array_info(obj1[key]), "NOT FOUND"))
            else:
                # 配列の場合は詳細情報を表示
                if isinstance(obj1[key], list) or isinstance(obj2[key], list):
                    info1 = get_array_info(obj1[key])
                    info2 = get_array_info(obj2[key])
                    if info1 != info2:
                        differences.append((new_path, info1, info2))
                    
                    # wavデータの場合、さらに詳細を確認
                    if 'wav' in new_path and isinstance(obj1[key], list) and isinstance(obj2[key], list):
                        if len(obj1[key]) > 0 and len(obj2[key]) > 0:
                            # 各要素の型を確認
                            if isinstance(obj1[key][0], list) and isinstance(obj2[key][0], list):
                                # 2次元配列の場合、各チャンネルの最初の要素を確認
                                for i in range(min(2, len(obj1[key]), len(obj2[key]))):
                                    if len(obj1[key][i]) > 0 and len(obj2[key][i]) > 0:
                                        elem1 = obj1[key][i][0]
                                        elem2 = obj2[key][i][0]
                                        if type(elem1) != type(elem2):
                                            differences.append((
                                                f"{new_path}[{i}][0]",
                                                f"{type(elem1).__name__}: {elem1 if not isinstance(elem1, list) else get_array_info(elem1)}",
                                                f"{type(elem2).__name__}: {elem2 if not isinstance(elem2, list) else get_array_info(elem2)}"
                                            ))
                
                # 辞書の場合は再帰的に比較
                elif isinstance(obj1[key], dict):
                    differences.extend(compare_structure(obj1[key], obj2[key], new_path))
    
    return differences

def main():
    # コマンドライン引数からファイルパスを取得
    if len(sys.argv) >= 3:
        success_path = Path(sys.argv[1])
        fail_path = Path(sys.argv[2])
    else:
        # デフォルトのファイルパス
        success_path = Path("/Users/neromehiro/hiro folder/my_Works/programing/all-in-one-music/test/success.json")
        fail_path = Path("/Users/neromehiro/hiro folder/my_Works/programing/all-in-one-music/ui/static/struct/0461_103additionalmemory.json")
    
    print("=" * 80)
    print("JSONファイル構造比較ツール")
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
    
    # JSONファイルを読み込み（一部のみ）
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
    print("=" * 80)
    print("トップレベルのキー比較")
    print("=" * 80)
    
    success_keys = set(success_data.keys())
    fail_keys = set(fail_data.keys())
    
    print(f"成功JSON: {sorted(success_keys)}")
    print(f"失敗JSON: {sorted(fail_keys)}")
    print()
    
    only_in_success = success_keys - fail_keys
    only_in_fail = fail_keys - success_keys
    
    if only_in_success:
        print(f"✅ 成功JSONのみ: {sorted(only_in_success)}")
    if only_in_fail:
        print(f"❌ 失敗JSONのみ: {sorted(only_in_fail)}")
    
    print()
    print("=" * 80)
    print("wav セクションの詳細分析")
    print("=" * 80)
    
    if 'wav' in success_data and 'wav' in fail_data:
        success_wav = success_data['wav']
        fail_wav = fail_data['wav']
        
        print("【成功JSON - wav構造】")
        for key in sorted(success_wav.keys()):
            info = get_array_info(success_wav[key])
            print(f"  wav.{key}: {info}")
            
            # さらに詳細を表示
            if isinstance(success_wav[key], list) and len(success_wav[key]) > 0:
                if isinstance(success_wav[key][0], list) and len(success_wav[key][0]) > 0:
                    first_elem = success_wav[key][0][0]
                    print(f"    └─ 最初の要素の型: {type(first_elem).__name__}")
                    if isinstance(first_elem, list):
                        print(f"       └─ 形状: {get_array_info(first_elem)}")
        
        print()
        print("【失敗JSON - wav構造】")
        for key in sorted(fail_wav.keys()):
            info = get_array_info(fail_wav[key])
            print(f"  wav.{key}: {info}")
            
            # さらに詳細を表示
            if isinstance(fail_wav[key], list) and len(fail_wav[key]) > 0:
                if isinstance(fail_wav[key][0], list) and len(fail_wav[key][0]) > 0:
                    first_elem = fail_wav[key][0][0]
                    print(f"    └─ 最初の要素の型: {type(first_elem).__name__}")
                    if isinstance(first_elem, list):
                        print(f"       └─ 形状: {get_array_info(first_elem)}")
    
    print()
    print("=" * 80)
    print("構造の違い一覧")
    print("=" * 80)
    
    differences = compare_structure(success_data, fail_data)
    
    if differences:
        # 最大幅を計算
        max_path_len = max(len(d[0]) for d in differences)
        max_success_len = max(len(d[1]) for d in differences)
        
        print(f"{'パス':<{max_path_len}} | {'成功JSON':<{max_success_len}} | 失敗JSON")
        print("-" * (max_path_len + max_success_len + 20))
        
        for path, success_info, fail_info in differences:
            # wavセクションの違いをハイライト
            if 'wav' in path:
                print(f"⚠️  {path:<{max_path_len}} | {success_info:<{max_success_len}} | {fail_info}")
            else:
                print(f"   {path:<{max_path_len}} | {success_info:<{max_success_len}} | {fail_info}")
    else:
        print("✅ 構造に違いはありません")
    
    print()
    print("=" * 80)
    print("問題の診断")
    print("=" * 80)
    
    # Waveformコンポーネントが期待する形式をチェック
    if 'wav' in fail_data:
        fail_wav = fail_data['wav']
        
        # Waveformが期待するキーの存在確認
        expected_keys = ['low', 'mid', 'high']
        actual_keys = list(fail_wav.keys())
        
        if set(expected_keys) != set(actual_keys):
            print("❌ Waveformコンポーネントの期待と実際のキーが異なります:")
            print(f"   期待: {expected_keys}")
            print(f"   実際: {actual_keys}")
            print()
            print("   → Waveformは low/mid/high を期待していますが、")
            print("     実際のデータは drum/bass/vocal/other を持っています")
        
        # データ形式の確認
        for key in fail_wav.keys():
            data = fail_wav[key]
            if isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], list):
                    print(f"\n📊 wav.{key} は2次元配列です:")
                    print(f"   チャンネル数: {len(data)}")
                    if len(data[0]) > 0:
                        print(f"   サンプル数: {len(data[0])}")
                        print(f"   最初の要素の型: {type(data[0][0]).__name__}")

if __name__ == "__main__":
    main()
