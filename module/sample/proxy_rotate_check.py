import asyncio
import logging
from playwright.async_api import async_playwright
import requests

logging.basicConfig(level=logging.INFO)

def get_rotating_proxy() -> str:
    """Webshare APIを使って、ランダムなプロキシIPを取得します"""
    response = requests.get(
        "https://ipv4.webshare.io/",  # WebshareのプロキシAPIエンドポイント
        proxies={
            "http": "http://oaghpvrh-rotate:ak24ante1ua4@p.webshare.io:80/",
            "https": "http://oaghpvrh-rotate:ak24ante1ua4@p.webshare.io:80/"
        }
    )
    if response.status_code == 200:
        # レスポンスの例: "109.107.243.141"
        return response.text.strip()
    else:
        logging.error("プロキシの取得に失敗しました")
        return None

async def check_ip_with_proxy_and_sleep(proxy_url: str, username: str, password: str) -> str:
    """
    プロキシを使って、現在のIPアドレスを取得し、1時間待機する。
    """
    async with async_playwright() as playwright:
        # ブラウザ起動オプション
        browser_args = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--blink-settings=imagesEnabled=false',
            '--host-resolver-rules=MAP copilot.microsoft.com 127.0.0.1',
            '--disable-blink-features=AutomationControlled',
        ]
        browser_launch_options = {
            "headless": False,
            "args": browser_args,
        }

        # ブラウザ起動
        browser = await playwright.chromium.launch(**browser_launch_options)

        # プロキシ設定
        proxy_info = {
            "server": f"http://{proxy_url}:80",
            "username": username,
            "password": password
        }
        print("proxy_info")
        print(proxy_info)

        # コンテキスト作成
        context = await browser.new_context(proxy=proxy_info)

        # ページを開く
        page = await context.new_page()

        # httpbinを使ってIPアドレスを取得
        response = await page.goto("https://httpbin.org/ip")
        ip_info = await response.json()

        # IPアドレスを取得
        current_ip = ip_info.get("origin", "IPの取得に失敗しました")
        logging.info(f"現在のIPアドレス（プロキシ経由）: {current_ip}")

        # 1時間待機（60分間）
        logging.info("1時間待機します...")
        await asyncio.sleep(60 * 60)  # 1時間待機

        # ブラウザを閉じる
        await browser.close()

        return current_ip

if __name__ == "__main__":
    proxy_url_input = get_rotating_proxy()  # 動的にプロキシを取得
    if proxy_url_input:
        username_input = "oaghpvrh-rotate"
        password_input = "ak24ante1ua4"

        # 非同期実行
        loop = asyncio.get_event_loop()
        ip_address = loop.run_until_complete(check_ip_with_proxy_and_sleep(proxy_url_input, username_input, password_input))

        print(f"現在のIPアドレス（プロキシ経由）: {ip_address}")
