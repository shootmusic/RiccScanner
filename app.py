#!/usr/bin/env python3
"""
RiccScanner Backend - OpenAI GPT-4 Vision Edition
"""

import os
import io
import base64
import requests
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Ambil dari environment variable
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

HTML_FRONTEND = '''
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RiccScanner - Math Solver</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            background: #0d1117; 
            color: #c9d1d9; 
            font-family: 'Segoe UI', Arial, sans-serif;
            padding: 20px;
            min-height: 100vh;
        }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { 
            color: #f85149; 
            text-align: center; 
            margin-bottom: 10px;
            font-size: 32px;
            font-weight: bold;
        }
        .subtitle { 
            color: #8b949e; 
            text-align: center; 
            margin-bottom: 30px;
            font-size: 14px;
        }
        .camera-box {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        video, #preview {
            width: 100%;
            border-radius: 8px;
            background: #010409;
            display: block;
            margin-bottom: 15px;
        }
        .btn {
            width: 100%;
            padding: 15px;
            margin: 10px 0;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-scan { 
            background: #f85149;
            color: white;
        }
        .btn-scan:hover { background: #ff7b72; }
        .btn-file {
            background: #238636;
            color: white;
            display: block;
            text-align: center;
        }
        .btn-file:hover { background: #2ea043; }
        .result-box {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
            display: none;
        }
        .result-box h2 { 
            color: #58a6ff; 
            margin-bottom: 15px; 
            font-size: 18px;
            font-weight: bold;
        }
        .result-text {
            background: #0d1117;
            padding: 15px;
            border-radius: 6px;
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            line-height: 1.6;
            font-size: 14px;
            color: #c9d1d9;
            border-left: 3px solid #58a6ff;
        }
        .loading {
            color: #58a6ff;
            text-align: center;
            display: none;
            padding: 20px;
            font-size: 14px;
        }
        input[type="file"] { display: none; }
        .status {
            text-align: center;
            color: #8b949e;
            font-size: 12px;
            margin-top: 10px;
            font-family: monospace;
        }
        .footer {
            text-align: center;
            color: #484f58;
            font-size: 11px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #30363d;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>RiccScanner</h1>
        <p class="subtitle">Math OCR Solver - Powered by GPT-4 Vision</p>
        
        <div class="camera-box">
            <video id="video" autoplay playsinline></video>
            <canvas id="canvas" style="display:none;"></canvas>
            <img id="preview" style="display:none;">
            
            <button class="btn btn-scan" onclick="scan()">SCAN SOAL</button>
            
            <label class="btn btn-file">
                PILIH GAMBAR DARI GALLERY
                <input type="file" id="fileInput" accept="image/*" onchange="loadFile(event)">
            </label>
            
            <p class="loading" id="loading">Processing with GPT-4 Vision...</p>
            <p class="status" id="status">Status: Ready | Kamera: Loading...</p>
        </div>
        
        <div class="result-box" id="resultBox">
            <h2>HASIL ANALISIS</h2>
            <div class="result-text" id="result"></div>
        </div>
        
        <div class="footer">
            RiccScanner | Powered by OpenAI GPT-4 Vision
        </div>
    </div>

    <script>
        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        const preview = document.getElementById('preview');
        const loading = document.getElementById('loading');
        const status = document.getElementById('status');
        
        navigator.mediaDevices.getUserMedia({ 
            video: { 
                facingMode: 'environment',
                width: { ideal: 1920 },
                height: { ideal: 1080 }
            } 
        })
        .then(stream => {
            video.srcObject = stream;
            status.textContent = 'Status: Ready | Kamera: Aktif';
        })
        .catch(err => {
            status.textContent = 'Status: Kamera error - ' + err.message;
            video.style.display = 'none';
        });
        
        function scan() {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            
            const imageData = canvas.toDataURL('image/jpeg', 0.9);
            sendToServer(imageData);
        }
        
        function loadFile(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = e => {
                preview.src = e.target.result;
                preview.style.display = 'block';
                video.style.display = 'none';
                sendToServer(e.target.result);
            };
            reader.readAsDataURL(file);
        }
        
        function sendToServer(imageData) {
            loading.style.display = 'block';
            status.textContent = 'Status: Processing with AI...';
            
            fetch('/solve', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({image: imageData})
            })
            .then(r => {
                if (!r.ok) throw new Error('HTTP ' + r.status);
                return r.json();
            })
            .then(data => {
                loading.style.display = 'none';
                document.getElementById('resultBox').style.display = 'block';
                document.getElementById('result').textContent = data.result;
                status.textContent = 'Status: Complete';
            })
            .catch(err => {
                loading.style.display = 'none';
                status.textContent = 'Status: Error';
                alert('Error: ' + err.message);
            });
        }
    </script>
</body>
</html>
'''

def solve_math(expression):
    """Solve ekspresi matematika"""
    try:
        import sympy as sp
        
        expr = expression.replace('×', '*').replace('÷', '/').replace('^', '**')
        expr = expr.replace(' ', '')
        
        if '=' in expr:
            left, right = expr.split('=', 1)
            eq = sp.Eq(sp.sympify(left), sp.sympify(right))
            sol = sp.solve(eq)
            return f"Persamaan: {expression}\nSolusi: {sol}"
        
        result = sp.sympify(expr)
        simplified = sp.simplify(result)
        numeric = float(result.evalf())
        
        return f"Ekspresi: {expression}\nHasil: {numeric}\nSimplifikasi: {simplified}"
        
    except Exception as e:
        return f"Ekspresi: {expression}\nError: {str(e)}"

def gpt4_vision_ocr(image_base64):
    """OCR pakai GPT-4 Vision"""
    if not OPENAI_API_KEY:
        return "ERROR: API key not configured"
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    if ',' in image_base64:
        image_base64 = image_base64.split(',')[1]
    
    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Baca soal matematika di gambar ini. Tulis HANYA ekspresi matematikanya saja, tanpa penjelasan. Contoh: 50+100*2000 atau 5*x+10=20. Jika tidak ada soal matematika, tulis 'NO_MATH'."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 100
    }
    
    try:
        response = requests.post(OPENAI_URL, headers=headers, json=payload, timeout=30)
        result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            text = result['choices'][0]['message']['content'].strip()
            return text
        else:
            return "ERROR: " + str(result.get('error', result))
            
    except Exception as e:
        return f"ERROR: {str(e)}"

@app.route('/')
def index():
    return render_template_string(HTML_FRONTEND)

@app.route('/solve', methods=['POST'])
def solve():
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'result': 'Error: No image data'}), 400
        
        image_data = data['image']
        
        detected = gpt4_vision_ocr(image_data)
        
        if detected == 'NO_MATH':
            return jsonify({
                'result': 'Tidak terdeteksi soal matematika.\n\nTips:\n- Tulis dengan jelas\n- Pastikan pencahayaan cukup\n- Hindari background berantakan'
            })
        
        if detected.startswith('ERROR'):
            return jsonify({
                'result': f'OCR Error: {detected}\n\nCoba lagi dengan gambar lebih jelas.'
            })
        
        solution = solve_math(detected)
        
        return jsonify({
            'result': f"Terdeteksi: {detected}\n\n{solution}"
        })
        
    except Exception as e:
        return jsonify({
            'result': f'Server Error: {str(e)}'
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"RiccScanner GPT-4 Edition - Port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
