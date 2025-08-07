from playwright.sync_api import sync_playwright
import time

def check_proxy(proxy_info, use_proxy=True):
    # Playwrightでブラウザを起動
    with sync_playwright() as p:
        browser_args = {}
        
        # プロキシ設定
        if use_proxy:
            browser_args = {
                "proxy": {
                    "server": f'http://{proxy_info["server"]}',
                    "username": proxy_info['username'],
                    "password": proxy_info['password']
                }
            }
        print("proxy")
        print(f'http://{proxy_info["server"]}')
        # ブラウザを起動
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(**browser_args)
        
        # 新しいページを開く
        page = context.new_page()
        
        # 接続テスト用URL
        test_url = 'https://httpbin.org/ip'
        
        try:
            # リクエスト前の時間を記録
            start_time = time.time()
            
            # ページを開いてレスポンスを取得
            page.goto(test_url)
            
            # レスポンス後の時間を記録
            end_time = time.time()
            
            # レスポンス時間の計算
            response_time = end_time - start_time
            
            # レスポンス内容を取得
            response_content = page.content()
            
            print(f"接続成功！レスポンス時間: {response_time:.4f}秒")
            print("レスポンス内容:", response_content)
            
        except Exception as e:
            print("接続に失敗しました:", str(e))
        
        finally:
            browser.close()

# プロキシ情報
proxy_info = {
    'server': 'p.webshare.io',
    'username': 'oaghpvrh-rotate',
    'password': 'ak24ante1ua4'
}

# プロキシを使用したい場合
check_proxy(proxy_info, use_proxy=True)
