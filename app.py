from flask import Flask, request, Response, jsonify
import requests
import re
import os
from urllib.parse import urljoin, quote, unquote

app = Flask(__name__)

M3U_SOURCE_URL = "https://tight-firefly-ecdd.poonamchouhan076.workers.dev/"

def get_parsed_channels(base_url):
    try:
        response = requests.get(M3U_SOURCE_URL, timeout=10)
        if response.status_code != 200:
            return []
        
        lines = response.text.splitlines()
        channels = []
        current_channel = {}
        channel_index = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("#EXTINF:"):
                current_channel = {}
                logo_match = re.search(r'tvg-logo="([^"]+)"', line)
                current_channel["logo"] = logo_match.group(1) if logo_match else ""
                
                parts = line.split(",")
                current_channel["title"] = parts[-1].strip() if len(parts) > 1 else "Unknown Channel"
                    
            elif not line.startswith("#"):
                if current_channel and "title" in current_channel:
                    raw_link = line
                    channel_index += 1
                    safe_slug = re.sub(r'[^a-zA-Z0-9]', '_', current_channel["title"]).lower()
                    slug = f"{safe_slug}_{channel_index}"
                    
                    channels.append({
                        "title": current_channel["title"],
                        "logo": current_channel["logo"],
                        "slug": slug,
                        "m3u8": f"{base_url}/live/{slug}.m3u8",
                        "raw_link": raw_link
                    })
                    current_channel = {}
        return channels
    except Exception:
        return []

@app.route('/')
def home():
    return "PRT Stream Clean Proxy & Embed Server is Running!"

@app.route('/channels', methods=['GET'])
def get_channels():
    base_url = request.host_url.rstrip('/')
    channels_data = get_parsed_channels(base_url)
    
    clean_channels = []
    for ch in channels_data:
        clean_channels.append({
            "title": ch["title"],
            "logo": ch["logo"],
            "m3u8": ch["m3u8"]
        })
        
    return jsonify({
        "status": "success",
        "total_channels": len(clean_channels),
        "channels": clean_channels
    })

@app.route('/live/<filename>', methods=['GET'])
def serve_custom_m3u8(filename):
    slug = filename.rsplit('.', 1)[0]
    base_url = request.host_url.rstrip('/')
    
    channels_data = get_parsed_channels(base_url)
    target_url = None
    for ch in channels_data:
        if ch["slug"] == slug:
            target_url = ch["raw_link"]
            break
            
    if not target_url:
        return "Channel not found", 404
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.0.0 Mobile Safari/537.36",
        "Referer": "https://www.sonyliv.com/",
        "Origin": "https://www.sonyliv.com",
        "Accept": "*/*",
        "Connection": "keep-alive"
    }
    
    try:
        resp = requests.get(target_url, headers=headers, stream=True, timeout=15)
        if resp.status_code != 200:
            return f"Upstream Error: {resp.status_code}", resp.status_code
        
        content_text = resp.text
        rewritten_lines = []
        
        for line in content_text.splitlines():
            line = line.strip()
            if not line:
                continue
            
            if not line.startswith("#"):
                absolute_segment_url = urljoin(target_url, line)
                proxied_segment_url = f"{base_url}/proxy_seg?url={quote(absolute_segment_url, safe='')}"
                rewritten_lines.append(proxied_segment_url)
            else:
                rewritten_lines.append(line)
                
        final_playlist = "\n".join(rewritten_lines)
        return Response(final_playlist, status=200, content_type="application/vnd.apple.mpegurl")
        
    except Exception as e:
        return str(e), 500

@app.route('/proxy_seg', methods=['GET'])
def proxy_seg():
    encoded_url = request.args.get('url')
    if not encoded_url:
        return "Missing URL", 400
    target_url = unquote(encoded_url)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.0.0 Mobile Safari/537.36",
        "Referer": "https://www.sonyliv.com/",
        "Origin": "https://www.sonyliv.com",
        "Accept": "*/*",
        "Connection": "keep-alive"
    }
    
    try:
        resp = requests.get(target_url, headers=headers, stream=True, timeout=15)
        return Response(
            resp.iter_content(chunk_size=4096),
            status=resp.status_code,
            content_type=resp.headers.get('content-type', 'video/mp2t')
        )
    except Exception as e:
        return str(e), 500

@app.route('/embed_player', methods=['GET'])
def embed_player():
    channel_id = request.args.get('id', 'sony-hd')
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
        
        # उनका लोगो हटाकर अपना PRT Stream वाला लोगो लिंक यहाँ डाल दे भाई
        my_logo_url = "https://i.ibb.co/4wPT214r/frame.png" 
        html_content = html_content.replace(
            "https://allinonereborn2.online/logo/allinonet.jpg", 
            my_logo_url
        )
        
        return Response(html_content, status=200, content_type="text/html")
        
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
