#!/usr/bin/env python3
"""
JSONファイルの内容を俯瞰的に確認するためのサマライザー
大きなJSONファイルの各キーの値を先着10個まで取得して、
構造を把握しやすい形式で出力する
"""

import json
import os
import sys
from typing import Any, Dict, List, Union
from pathlib import Path


def summarize_value(value: Any, max_items: int = 10) -> Any:
    """
    値をサマライズする
    - リストの場合: 最初のmax_items個まで取得
    - 辞書の場合: 再帰的にサマライズ
    - その他: そのまま返す
    """
    if isinstance(value, list):
        # リストの場合、最初のmax_items個まで取得
        sample = value[:max_items]
        result = {
            "_type": "list",
            "_total_count": len(value),
            "_sample_count": len(sample),
            "_samples": sample
        }
        
        # リストの要素が辞書の場合、それもサマライズ
        if sample and isinstance(sample[0], dict):
            result["_structure_sample"] = summarize_value(sample[0], max_items)
            
        return result
        
    elif isinstance(value, dict):
        # 辞書の場合、各キーに対して再帰的にサマライズ
        result = {}
        for key, val in value.items():
            result[key] = summarize_value(val, max_items)
        return result
        
    else:
        # プリミティブ型の場合はそのまま返す
        return value


def create_summary(data: Dict[str, Any], max_items: int = 10) -> Dict[str, Any]:
    """
    JSONデータ全体のサマリーを作成
    """
    summary = {
        "_metadata": {
            "description": "JSONファイルのサマリー（各配列は最初の10個まで）",
            "max_items_per_array": max_items,
            "legend": {
                "_type": "データ型",
                "_total_count": "配列の総要素数",
                "_sample_count": "サンプルとして取得した要素数",
                "_samples": "サンプルデータ",
                "_structure_sample": "配列要素が辞書の場合の構造サンプル"
            }
        },
        "summary": summarize_value(data, max_items)
    }
    
    return summary


def process_json_file(input_path: str, output_dir: str = None) -> str:
    """
    JSONファイルを読み込んでサマリーを作成し、出力する
    """
    input_path = Path(input_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"ファイルが見つかりません: {input_path}")
    
    if not input_path.suffix == '.json':
        raise ValueError(f"JSONファイルではありません: {input_path}")
    
    # 出力ディレクトリの設定
    if output_dir:
        output_dir = Path(output_dir)
    else:
        output_dir = input_path.parent
    
    # 出力ファイル名の生成
    output_filename = f"summarize_{input_path.stem}.json"
    output_path = output_dir / output_filename
    
    print(f"処理中: {input_path}")
    print(f"ファイルサイズ: {input_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    # JSONファイルの読み込み
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSONの解析に失敗しました: {e}")
    
    # サマリーの作成
    print("サマリーを作成中...")
    summary = create_summary(data)
    
    # サマリーの保存
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"サマリーを保存しました: {output_path}")
    print(f"出力ファイルサイズ: {output_path.stat().st_size / 1024:.2f} KB")
    
    return str(output_path)


def main():
    """
    コマンドラインインターフェース
    """
    if len(sys.argv) < 2:
        print("使用方法: python json_summarizer.py <JSONファイルパス> [出力ディレクトリ]")
        print("例: python json_summarizer.py module/sample_data/success_data.json")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        output_path = process_json_file(input_path, output_dir)
        print(f"\n✅ 処理が完了しました！")
        print(f"サマリーファイル: {output_path}")
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
