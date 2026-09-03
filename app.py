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
    return "PRT Stream SonyLIV Rewriter & Proxy is Running!"

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
                    # चैनल के मास्टर लिंक को भी प्रॉक्सी से गुजारेंगे ताकि .m3u8 फाइल रीराइट हो सके
                    rewritten_link = f"{base_url}/stream_proxy?url={quote(raw_link, safe='')}"
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
        
        # अगर यह फाइल `.m3u8` है, तो इसके अंदर के चंक्स को रीराइट करना पड़ेगा!
        if '.m3u8' in target_url or 'm3u8' in resp.headers.get('content-type', ''):
            content_text = resp.text
            base_url = request.host_url.rstrip('/')
            rewritten_lines = []
            
            for line in content_text.splitlines():
                line = line.strip()
                if not line:
                    continue
                
                # अगर लाइन कोई यूआरएल या चंक फाइल है (जो # से शुरू नहीं होती)
                if not line.startswith("#"):
                    # अगर लिंक रिलेटिव है तो उसे टारगेट यूआरएल के हिसाब से पूरा बनाओ
                    absolute_segment_url = urljoin(target_url, line)
                    # फिर उसे हमारे प्रॉक्सी के जरिए लूप में डालो
                    proxied_segment_url = f"{base_url}/stream_proxy?url={quote(absolute_segment_url, safe='')}"
                    rewritten_lines.append(proxied_segment_url)
                else:
                    rewritten_lines.append(line)
                    
            final_playlist = "\n".join(rewritten_lines)
            return Response(final_playlist, status=200, content_type="application/vnd.apple.mpegurl")
        
        else:
            # अगर यह असली वीडियो का टुकड़ा (.ts या .m4s) है, तो इसे सीधे प्लेयर को पास कर दो
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
