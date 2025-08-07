# module/sample/test_db_async.py
import asyncio
import aiomysql
import ssl
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
            
            # データベース名のキーを変換（database → db）
            if 'database' in db_credentials:
                db_credentials['db'] = db_credentials.pop('database')
                
            # SSLコンテキストの設定
            if db_credentials.get('ssl_verify_cert', False):
                db_credentials['ssl'] = ssl.create_default_context()
                if 'ssl_ca' in db_credentials:
                    db_credentials['ssl'].load_verify_locations(db_credentials['ssl_ca'])
                    db_credentials.pop('ssl_ca')
            else:
                db_credentials['ssl'] = ssl._create_unverified_context()
                
            # 不要なキーを削除
            for key in ['ssl_verify_cert', 'pool_name', 'pool_size']:
                if key in db_credentials:
                    db_credentials.pop(key)
                    
            return db_credentials
        except json.JSONDecodeError as e:
            print(f"AZURE_APP_SETTINGSの解析エラー: {e}")
    
    # 直接DB_CREDENTIALSから設定を取得（フォールバック）
    db_credentials_str = os.getenv('DB_CREDENTIALS')
    if db_credentials_str:
        try:
            db_credentials = json.loads(db_credentials_str)
            
            # データベース名のキーを変換（database → db）
            if 'database' in db_credentials:
                db_credentials['db'] = db_credentials.pop('database')
                
            # SSLコンテキストの設定
            if db_credentials.get('ssl_verify_cert', False):
                db_credentials['ssl'] = ssl.create_default_context()
                if 'ssl_ca' in db_credentials:
                    db_credentials['ssl'].load_verify_locations(db_credentials['ssl_ca'])
                    db_credentials.pop('ssl_ca')
            else:
                db_credentials['ssl'] = ssl._create_unverified_context()
                
            # 不要なキーを削除
            for key in ['ssl_verify_cert', 'pool_name', 'pool_size']:
                if key in db_credentials:
                    db_credentials.pop(key)
                    
            return db_credentials
        except json.JSONDecodeError as e:
            print(f"DB_CREDENTIALSの解析エラー: {e}")
    
    # 環境変数が設定されていない場合のデフォルト設定
    print("警告: 環境変数からデータベース設定を取得できませんでした。デフォルト設定を使用します。")
    return {
        "host": "localhost",
        "user": "root",
        "password": "",
        "db": "test",
        "port": 3306,
        "ssl": None,
        "autocommit": True
    }

# データベース接続設定を取得
DB_CONFIG = get_db_config()

async def get_connection_pool():
    """非同期コネクションプールを作成"""
    try:
        pool = await aiomysql.create_pool(**DB_CONFIG)
        return pool
    except aiomysql.Error as e:
        print(f"コネクションプールの作成に失敗しました: {e}")
        raise

async def fetch_first_record(pool):
    """最初のレコードを取得"""
    query = "SELECT id, url, content, created_at FROM html_contents ORDER BY id ASC LIMIT 1"
    async with pool.acquire() as connection:
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query)
            result = await cursor.fetchone()
            return result

async def main():
    pool = await get_connection_pool()
    first_record = await fetch_first_record(pool)
    if first_record:
        print("最初のレコード:")
        print(f"ID: {first_record['id']}")
        print(f"URL: {first_record['url']}")
        print(f"Content: {first_record['content'][:100]}...")  # コンテンツの最初の100文字のみ表示
        print(f"Created At: {first_record['created_at']}")
    else:
        print("レコードが見つかりませんでした。")
    pool.close()
    await pool.wait_closed()

# 非同期関数を実行
asyncio.run(main())
