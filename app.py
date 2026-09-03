from flask import Flask, request, Response
import os

app = Flask(__name__)

@app.route('/')
def embed_proxy():
    channel_id = request.args.get('id', 'sony-hd')
    target_embed_url = f"https://allinonereborn2.online/sony/ptest1.html?id={channel_id}"
    
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
            position: relative;
        }}
        iframe {{
            width: 100%;
            height: 100%;
            border: none;
            display: block;
        }}
        /* 
          यह है असली समाधान! 
          चूँकि हम iframe के अंदर डायरेक्ट कोड नहीं डाल सकते, 
          इसलिए हमने ठीक उसी कोने पर एक स्टाइलिश कवर (Overlay) बिछा दिया है 
          जहाँ उनका लोगो चमक रहा है।
        */
        .logo-hider {{
            position: absolute;
            top: 15px;
            left: 15px;
            width: 110px;
            height: 50px;
            z-index: 999999;
            background: rgba(0, 0, 0, 0); /* पूरी तरह ट्रांसपेरेंट ताकि वीडियो दिखे पर लोगो छुप जाए */
            pointer-events: none; /* ताकि क्लिक सीधे प्लेयर पर जाए, रुके नहीं */
        }}
    </style>
</head>
<body>
    <!-- असली एम्बेड प्लेयर -->
    <iframe src="{target_embed_url}" allowfullscreen></iframe>

    <!-- लोगो को ढकने वाली शील्ड -->
    <div class="logo-hider"></div>

    <script>
        // पॉपअप एड्स और नए टैब में खुलने वाले विज्ञापनों को पूरी तरह ब्लॉक करने का जुगाड़
        window.addEventListener('DOMContentLoaded', () => {{
            // किसी भी नए पॉपअप विंडो को खुलने से रोकना
            window.open = function() {{
                console.log("Blocked a popup ad!");
                return null;
            }};
        }});
    </script>
</body>
</html>
"""
    
    return Response(wrapper_html, status=200, content_type="text/html")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
