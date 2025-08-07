
# DBの操作のサンプルコード
import mysql.connector
from mysql.connector import pooling
import time
import os
import json
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

# 環境変数からデータベース設定を取得
def get_db_config():
    # AZURE_APP_SETTINGSから設定を取得
    azure_app_settings_str = os.getenv('AZURE_APP_SETTINGS')
    if azure_app_settings_str:
        try:
            azure_app_settings = json.loads(azure_app_settings_str)
            db_credentials = azure_app_settings.get('DB_CREDENTIALS', {})
            return db_credentials
        except json.JSONDecodeError as e:
            print(f"AZURE_APP_SETTINGSの解析エラー: {e}")
    
    # 直接DB_CREDENTIALSから設定を取得（フォールバック）
    db_credentials_str = os.getenv('DB_CREDENTIALS')
    if db_credentials_str:
        try:
            db_credentials = json.loads(db_credentials_str)
            return db_credentials
        except json.JSONDecodeError as e:
            print(f"DB_CREDENTIALSの解析エラー: {e}")
    
    # 環境変数が設定されていない場合のデフォルト設定
    print("警告: 環境変数からデータベース設定を取得できませんでした。デフォルト設定を使用します。")
    return {
        "host": "localhost",
        "user": "root",
        "password": "",
        "database": "test",
        "port": 3306,
        "autocommit": True,
        "pool_name": "mypool",
        "pool_size": 1
    }

# データベース接続設定を取得
DB_CONFIG = get_db_config()


def get_connection_pool():
    """コネクションプールを作成"""
    try:
        pool = pooling.MySQLConnectionPool(**DB_CONFIG)
        return pool
    except mysql.connector.Error as e:
        print(f"コネクションプールの作成に失敗しました: {e}")
        raise

def fetch_first_record(pool):
    """最初のレコードを取得"""
    query = "SELECT id, url, content, created_at FROM html_contents ORDER BY id ASC LIMIT 1"
    try:
        connection = pool.get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchone()
        return result
    except mysql.connector.Error as e:
        print(f"レコードの取得に失敗しました: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

if __name__ == "__main__":
    start_time = time.time()
    pool = get_connection_pool()
    first_record = fetch_first_record(pool)
    elapsed_time = time.time() - start_time
    if first_record:
        print("最初のレコード:")
        print(f"ID: {first_record['id']}")
        print(f"URL: {first_record['url']}")
        print(f"Content: {first_record['content'][:100]}...")  # コンテンツの最初の100文字のみ表示
        print(f"Created At: {first_record['created_at']}")
    else:
        print("レコードが見つかりませんでした。")
    print(f"処理時間: {elapsed_time:.2f} 秒")
