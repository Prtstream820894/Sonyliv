from flask import Flask, request, Response
import requests

# (बाकी पुराना Flask कोड वैसा का वैसा रहेगा, बस नीचे वाला रूट जोड़ना है)

@app.route('/embed_player', methods=['GET'])
def embed_player():
    channel_id = request.args.get('id', 'sony-hd')
    
    # उस साइट का असली एम्बेड पेज फेच कर रहे हैं
    target_page_url = f"https://allinonereborn2.online/sony/ptest1.html?id={channel_id}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.0.0 Mobile Safari/537.36",
        "Referer": "https://allinonereborn2.online/"
    }
    
    try:
        resp = requests.get(target_page_url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return f"Failed to load player: {resp.status_code}", resp.status_code
        
        html_content = resp.text
        
        # 1. उनका लोगो का URL बदलकर अपना खुद का लोगो लगा दो (या खाली छोड़ दो)
        # यहाँ अपना खुद का लोगो लिंक डाल सकता है भाई:
        my_logo_url = "https://i.ibb.co/4wPT214r/frame.png" # तेरी पसंद का लोगो लिंक
        
        html_content = html_content.replace(
            "https://allinonereborn2.online/logo/allinonet.jpg", 
            my_logo_url
        )
        
        # 2. अगर उनका एडब्लॉकर वाला पॉपअप या कोई फालतू स्क्रिप्ट हटानी हो, तो वो भी यहाँ से कंट्रोल कर सकते हैं
        
        return Response(html_content, status=200, content_type="text/html")
        
    except Exception as e:
        return str(e), 500
