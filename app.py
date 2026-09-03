from flask import Flask, jsonify, request
import requests
import re
import os

app = Flask(__name__)

# तेरी M3U प्लेलिस्ट का असली सोर्स लिंक
M3U_SOURCE_URL = "https://tight-firefly-ecdd.poonamchouhan076.workers.dev/"

@app.route('/')
def home():
    return "PRT Stream SonyLIV Rewriter is Running!"

@app.route('/channels', methods=['GET'])
def get_channels():
    try:
        # 1. वर्कर से M3U प्लेलिस्ट फेच करना
        response = requests.get(M3U_SOURCE_URL, timeout=10)
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch playlist"}), 500
        
        m3u_content = response.text
        channels = []
        
        # 2. M3U डेटा को पार्स करने के लिए लाइन्स में तोड़ना
        lines = m3u_content.splitlines()
        current_channel = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # जब लाइन #EXTINF से शुरू हो (चैनल की जानकारी)
            if line.startswith("#EXTINF:"):
                current_channel = {}
                
                # लोगो निकालना (tvg-logo)
                logo_match = re.search(r'tvg-logo="([^"]+)"', line)
                if logo_match:
                    current_channel["logo"] = logo_match.group(1)
                else:
                    current_channel["logo"] = ""
                
                # चैनल का नाम निकालना (कमा के बाद वाला हिस्सा)
                parts = line.split(",")
                if len(parts) > 1:
                    current_channel["title"] = parts[-1].strip()
                else:
                    current_channel["title"] = "Unknown Channel"
                    
            # जब लाइन URL हो (जो # से शुरू नहीं होती)
            elif not line.startswith("#"):
                if current_channel and "title" in current_channel:
                    raw_link = line
                    
                    # 3. यहाँ हम असली लिंक को अपनी प्रॉक्सी/रीराइटर फॉर्मेट में बदल रहे हैं
                    rewritten_link = f"/stream_proxy?url={raw_link}"
                    
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

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
