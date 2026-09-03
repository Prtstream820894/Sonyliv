from flask import Flask, request, Response
import requests
import os

app = Flask(__name__)

@app.route('/')
def embed_player():
    # यूआरएल से सीधे चैनल आईडी उठाएंगे (जैसे ?id=sony-hd)
    channel_id = request.args.get('id', 'sony-hd')
    
    # यहाँ पूरी चैनल आईडी के साथ उसका असली एम्बेड लिंक बन रहा है
    target_page_url = f"https://allinonereborn2.online/sony/ptest1.html?id={channel_id}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.0.0 Mobile Safari/537.36",
        "Referer": "https://allinonereborn2.online/"
    }
    
    try:
        # उस एम्बेड पेज को चैनल आईडी के साथ डाउनलोड करेंगे
        resp = requests.get(target_page_url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return f"Failed to load embed: {resp.status_code}", resp.status_code
        
        html_content = resp.text
        
        # उनके लोगो के यूआरएल को ब्लॉक/गायब कर देंगे ताकि वो कभी लोड न हो
        target_logo_url = "https://allinonereborn2.online/logo/allinonet.jpg"
        html_content = html_content.replace(target_logo_url, "")
        
        return Response(html_content, status=200, content_type="text/html")
        
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
