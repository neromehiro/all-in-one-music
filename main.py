# main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import ssl
import aiomysql
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# .envからDB_CREDENTIALSを取得し、JSONとしてパース
db_credentials = os.getenv("DB_CREDENTIALS")
if not db_credentials:
    raise ValueError("DB_CREDENTIALS が環境変数に設定されていません。")
db_config = json.loads(db_credentials)

@app.on_event("startup")
async def startup_event():
    # ssl_ca が設定されていれば ssl_context を作成
    if db_config.get("ssl_ca"):
        ssl_context = ssl.create_default_context(cafile=db_config["ssl_ca"])
        # SSL証明書の検証設定
        ssl_verify_cert = db_config.get("ssl_verify_cert", True)
        if not ssl_verify_cert:
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
    else:
        ssl_context = None

    app.state.pool = await aiomysql.create_pool(
        host=db_config["host"],
        user=db_config["user"],
        password=db_config["password"],
        db=db_config["database"],
        port=int(db_config["port"]),
        ssl=ssl_context,
        autocommit=db_config.get("autocommit", False),
        minsize=1,
        maxsize=int(db_config.get("pool_size", 10)),
    )
    

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # または特定のオリジンを指定
    allow_credentials=True,
    allow_methods=["*"],  # すべてのメソッドを許可（GET, POST, OPTIONS など）
    allow_headers=["*"],  # 任意のヘッダーを許可
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)



#########


from datetime import datetime, timedelta
import os

APP_VERSION = os.environ.get("APP_VERSION", "Unknown")
DEPLOYMENT_TIME = os.environ.get("DEPLOYMENT_TIME", "Unknown")
COMMIT_MESSAGE = os.environ.get("COMMIT_MESSAGE", "No commit message")

@app.get("/")
def read_root():
    return {
        "最終デプロイ日時": format_time(DEPLOYMENT_TIME),
        "コミットメッセージ": COMMIT_MESSAGE
    }

def format_time(time_str):
    if time_str and time_str != "Unknown":
        try:
            deploy_time = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
            deploy_time_jst = deploy_time + timedelta(hours=9)
            return deploy_time_jst.strftime("デプロイ : %-m/%-d %-H:%M")
        except ValueError:
            return time_str
    return "不明"
