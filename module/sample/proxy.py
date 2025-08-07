import requests
response = requests.get(
    "https://ipv4.webshare.io/",
    proxies={
        "http": "http://oaghpvrh-rotate:ak24ante1ua4@p.webshare.io:80/",
        "https": "http://oaghpvrh-rotate:ak24ante1ua4@p.webshare.io:80/"
    }
)
print(response.text)

# レスポンスの例：109.107.243.141