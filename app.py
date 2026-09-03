from flask import Flask, jsonify, request, Response
import requests
import re
import os

app = Flask(__name__)

# तेरी M3U प्लेलिस्ट का असली सोर्स लिंक
M3U_SOURCE_URL = "https://tight-firefly-ecdd.poonamchouhan076.workers.dev/"

@app.route('/')
def home():
    return "PRT Stream SonyLIV Middleware is Running!"

@app.route('/channels', methods=['GET'])
def get_channels():
    try:
        response = requests.get(M3U_SOURCE_URL, timeout=10)
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch playlist"}), 500
        
        m3u_content = response.text
        channels = []
        base_url = request.host_url.rstrip('/')
        
        lines = m3u_content.splitlines()
        current_channel = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("#EXTINF:"):
                current_channel = {}
                logo_match = re.search(r'tvg-logo="([^"]+)"', line)
                if logo_match:
                    current_channel["logo"] = logo_match.group(1)
                else:
                    current_channel["logo"] = ""
                
                parts = line.split(",")
                if len(parts) > 1:
                    current_channel["title"] = parts[-1].strip()
                else:
                    current_channel["title"] = "Unknown Channel"
                    
            elif not line.startswith("#"):
                if current_channel and "title" in current_channel:
                    raw_link = line
                    rewritten_link = f"{base_url}/stream_proxy?url={raw_link}"
                    current_channel["m3u8"] = rewritten_link
                    channels.append(current_channel)
                    current_channel = {}
                    
        return jsonify({
            "status": "success",
            "total_channels": len(channels),
            "channels": channels
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/stream_proxy', methods=['GET'])
def stream_proxy():
    target_url = request.args.get('url')
    if not target_url:
        return "Missing URL parameter", 400
    
    try:
        # मोबाइल प्लेयर / एंड्रॉइड जैसी हेडर ताकि CDN ब्लॉक न करे
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.0.0 Mobile Safari/537.36",
            "Referer": "https://www.sonyliv.com/",
            "Origin": "https://www.sonyliv.com"
        }
        
        # असली Sony/Stream सर्वर से डेटा फेच करना
        resp = requests.get(target_url, headers=headers, stream=True, timeout=15)
        
        return Response(
            resp.iter_content(chunk_size=1024),
            status=resp.status_code,
            content_type=resp.headers.get('content-type', 'video/mp2t')
        )
        
    except Exception as e:
        return str(e), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
