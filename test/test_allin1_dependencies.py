#!/usr/bin/env python3
"""
All-In-One音楽分析ライブラリのテストスクリプト
不足しているライブラリを特定するために使用
"""

import sys
import subprocess

def check_and_install_package(package_name, import_name=None):
    """パッケージの存在確認とインストール"""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        print(f"✅ {package_name} は既にインストールされています")
        return True
    except ImportError:
        print(f"❌ {package_name} が見つかりません。インストールを試行します...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            print(f"✅ {package_name} のインストールが完了しました")
            return True
        except subprocess.CalledProcessError:
            print(f"❌ {package_name} のインストールに失敗しました")
            return False

def main():
    print("🎵 All-In-One音楽分析ライブラリの依存関係チェック")
    print("=" * 50)
    
    # 基本的な依存関係をチェック
    dependencies = [
        ("torch", "torch"),
        ("torchaudio", "torchaudio"),
        ("numpy", "numpy"),
        ("scipy", "scipy"),
        ("librosa", "librosa"),
        ("matplotlib", "matplotlib"),
        ("tqdm", "tqdm"),
    ]
    
    failed_packages = []
    
    for package, import_name in dependencies:
        if not check_and_install_package(package, import_name):
            failed_packages.append(package)
    
    # madmomの特別なインストール
    print("\n📦 madmomの特別インストールを試行...")
    try:
        import madmom
        print("✅ madmom は既にインストールされています")
    except ImportError:
        print("❌ madmom が見つかりません。GitHubから直接インストールします...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "git+https://github.com/CPJKU/madmom"
            ])
            print("✅ madmom のインストールが完了しました")
        except subprocess.CalledProcessError:
            print("❌ madmom のインストールに失敗しました")
            failed_packages.append("madmom")
    
    # allin1パッケージのインストール
    print("\n🎯 allin1パッケージのインストールを試行...")
    try:
        import allin1
        print("✅ allin1 は既にインストールされています")
    except ImportError:
        print("❌ allin1 が見つかりません。インストールします...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "allin1"])
            print("✅ allin1 のインストールが完了しました")
        except subprocess.CalledProcessError:
            print("❌ allin1 のインストールに失敗しました")
            failed_packages.append("allin1")
    
    print("\n" + "=" * 50)
    if failed_packages:
        print(f"❌ 以下のパッケージのインストールに失敗しました: {', '.join(failed_packages)}")
        return False
    else:
        print("✅ すべての依存関係が正常にインストールされました！")
        return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🚀 All-In-One分析を開始できます！")
    else:
        print("\n⚠️  一部のパッケージのインストールに問題があります。手動でインストールが必要かもしれません。")
