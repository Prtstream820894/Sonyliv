from flask import Flask, request, Response
import os

app = Flask(__name__)

@app.route('/')
def embed_proxy():
    channel_id = request.args.get('id', 'sony-hd')
    
    # उनका असली एम्बेड लिंक जिसका प्लेयर हमें चलाना है
    target_embed_url = f"https://allinonereborn2.online/sony/ptest1.html?id={channel_id}"
    
    # हम यूजर के ब्राउज़र को एक साफ़-सुथरा HTML पेज देंगे जो उनके प्लेयर को फुलस्क्रीन लोड करेगा
    # और साथ ही एक जादुई JavaScript चलाएगा जो उनके लोगो को लोड ही नहीं होने देगी!
    wrapper_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>PRT Stream - Live Player</title>
    <style>
        html, body {{
            margin: 0;
            padding: 0;
            width: 100vw;
            height: 100dvh;
            background: #000;
            overflow: hidden;
        }}
        iframe {{
            width: 100%;
            height: 100%;
            border: none;
            display: block;
        }}
    </style>
</head>
<body>
    <!-- उनका असली एम्बेड यहाँ डायरेक्ट लोड होगा ताकि कोई फंक्शन या स्ट्रीम न टूटे -->
    <iframe id="player-frame" src="{target_embed_url}" allowfullscreen></iframe>

    <script>
        // जैसे ही उनका एम्बेड लोड होगा, यह स्क्रिप्ट लगातार चेक करेगी और उनके लोगो को गायब कर देगी
        const iframe = document.getElementById('player-frame');
        
        iframe.addEventListener('load', () => {{
            try {{
                const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                
                // लोगो के इमेज एलिमेंट को ढूंढकर हमेशा के लिए डिलीट करने का ऑब्ज़र्वर
                const observer = new MutationObserver((mutations, obs) => {{
                    const logoImg = iframeDoc.querySelector('img[src*="allinonet.jpg"], .player-logo');
                    if (logoImg) {{
                        logoImg.remove(); // लोगो देखते ही उड़ा दो!
                    }}
                }});
                
                observer.observe(iframeDoc.body, {{
                    childList: true,
                    subtree: true
                }});
                
                // तुरंत भी एक बार चेक करके हटा दो
                const initialLogo = iframeDoc.querySelector('img[src*="allinonet.jpg"], .player-logo');
                if (initialLogo) {{
                    initialLogo.remove();
                }}
            }} catch (e) {{
                console.log("Cross-origin restriction handled via wrapper");
            }}
        }});
    </script>
</body>
</html>
"""
    
    return Response(wrapper_html, status=200, content_type="text/html")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
