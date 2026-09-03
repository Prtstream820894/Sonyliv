from flask import Flask, request, Response
import requests
import os

app = Flask(__name__)

@app.route('/')
def proxy_stream():
    url = request.args.get('url', '')
    
    if not url:
        return "Stream URL missing! Use ?url=YOUR_M3U8_LINK", 400

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.sonyliv.com/"
    }

    try:
        # सर्वर साइड से लिंक फेच करना
        resp = requests.get(url, headers=headers, stream=True, timeout=15)
        
        # अगर m3u8 प्लेलिस्ट है तो उसके अंदर के सेगमेंट लिंक्स को भी प्रॉक्सी से रूट करो
        if '.m3u8' in url or 'mpegurl' in resp.headers.get('content-type', ''):
            content = resp.text
            base_url = url.rsplit('/', 1)[0] + '/'
            
            new_lines = []
            for line in content.splitlines():
                line = line.strip()
                if not line:
                    continue
                if line.startswith('#'):
                    if 'URI="' in line:
                        import re
                        def replace_uri(m):
                            uri = m.group(1)
                            abs_uri = uri if uri.startswith('http') else base_url + uri
                            return f'URI="{request.host_url}?url={abs_uri}"'
                        line = re.sub(r'URI="([^"]+)"', replace_uri, line)
                    new_lines.append(line)
                else:
                    abs_line = line if line.startswith('http') else base_url + line
                    proxy_line = f"{request.host_url}?url={abs_line}"
                    new_lines.append(proxy_line)
            
            return Response("\n".join(new_lines), content_type="application/vnd.apple.mpegurl")
        
        # अगर .ts वीडियो सेगमेंट है तो उसे यूजर को पास कर दो
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        response_headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
        
        return Response(resp.content, status=resp.status_code, headers=response_headers)

    except Exception as e:
        return f"Proxy Error: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
