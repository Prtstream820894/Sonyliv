from flask import Flask, jsonify, request, Response
import requests
import re
import os
from urllib.parse import urljoin, quote, unquote

app = Flask(__name__)

# तेरी M3U प्लेलिस्ट का असली सोर्स लिंक
M3U_SOURCE_URL = "https://tight-firefly-ecdd.poonamchouhan076.workers.dev/"

@app.route('/')
def home():
    return "PRT Stream Custom M3U8 Rewriter & Proxy is Running!"

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
        
        channel_index = 0
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
                    # यहाँ असली लिंक को छिपाकर अपना खुद का वर्चुअल m3u8 लिंक बना रहे हैं!
                    channel_index += 1
                    safe_slug = re.sub(r'[^a-zA-Z0-9]', '_', current_channel["title"]).lower()
                    
                    # JSON में दिखने वाला तेरा खुद का लिंक
                    virtual_m3u8_link = f"{base_url}/live/{safe_slug}_{channel_index}.m3u8?url={quote(raw_link, safe='')}"
                    
                    current_channel["m3u8"] = virtual_m3u8_link
                    channels.append(current_channel)
                    current_channel = {}
                    
        return jsonify({
            "status": "success",
            "total_channels": len(channels),
            "channels": channels
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/live/<path:filename>', methods=['GET'])
def serve_custom_m3u8(filename):
    encoded_url = request.args.get('url')
    if not encoded_url:
        return "Missing URL parameter", 400
    
    target_url = unquote(encoded_url)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.0.0 Mobile Safari/537.36",
        "Referer": "https://www.sonyliv.com/",
        "Origin": "https://www.sonyliv.com"
    }
    
    try:
        resp = requests.get(target_url, headers=headers, stream=True, timeout=15)
        
        if resp.status_code != 200:
            return f"Upstream Error: {resp.status_code}", resp.status_code
        
        content_text = resp.text
        
        # अगर यह मास्टर या मीडिया M3U8 प्लेलिस्ट है, तो इसके अंदर के सेगमेंट्स को रीराइट करो
        if '.m3u8' in target_url or '#EXTM3U' in content_text:
            base_url = request.host_url.rstrip('/')
            rewritten_lines = []
            
            for line in content_text.splitlines():
                line = line.strip()
                if not line:
                    continue
                
                if not line.startswith("#"):
                    absolute_segment_url = urljoin(target_url, line)
                    # हर सेगमेंट (.ts या अगली प्लेलिस्ट) को भी हमारे प्रॉक्सी रूट पर मोड़ देंगे
                    proxied_segment_url = f"{base_url}/live/seg.m3u8?url={quote(absolute_segment_url, safe='')}"
                    rewritten_lines.append(proxied_segment_url)
                else:
                    rewritten_lines.append(line)
                    
            final_playlist = "\n".join(rewritten_lines)
            return Response(final_playlist, status=200, content_type="application/vnd.apple.mpegurl")
        
        else:
            # अगर प्लेयर सीधे .ts टुकड़े मांग रहा है, तो उन्हें चुपचाप पास कर दो
            return Response(
                resp.iter_content(chunk_size=4096),
                status=resp.status_code,
                content_type=resp.headers.get('content-type', 'video/mp2t')
            )
            
    except Exception as e:
        return str(e), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
